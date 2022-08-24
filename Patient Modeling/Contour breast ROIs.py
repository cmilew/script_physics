from connect import *
from tkinter import *
import tkinter.messagebox
import tkinter.ttk as ttk
import sys
import copy
import datetime

################################################################
# Version 1 : Création
# Version 1.01 : Corrections de bugs mineurs et ajout d'une fonctionnalité de fichier log (à compléter --> Version 1.1)
# Version 1.02 : Corrections de l'appel au PACS (fonction connection_pacs) suite au passage en RS9B (MaJ 1.1 : plus
#                nécessaire)
# Version 1.1 : Changement des couleurs des ROIs et changement de noms des protocoles suite au nouveau scanner
# Version 1.2 : Modification du script : le CT n'est plus récupéré du PACS, seul le RTStruct est importé
# Version 1.2.1 : Modification par CM : changement du Type de la ROI 'Scar' pour passer de 'Undefined' à
#                 'IrradiatedVolume'. On lui met comme organ type 'Target'. (l. 394-395)
# Version 1.2.2 : Modification par CM : oubli de "Scar_L" et "Scar_R" qui n'étaient pas en OrganType "Target"
#                   (seulement "Scar"), ajout l.360-361.
#                Ajout de la ROI "External - PTV TOT" car nécessaire pour tous les template de clinical goals
#                (3D, rIMRT et VMAT)
# Version 1.2.3 : Modification par CM : mis à jour du script pour la 10B (modification dans l'architecture du statetree
#                 ui l.504_507)
# Version 1.2.4 : Modification par CM : mettre RemoveHoles3D à False dans la fonction SimplifyContours pour éviter que
#                 cela supprime certaines coupes d'OARs qui sont inclues dans des organes.
# Version 1.3 : Modification du script de manière à ce qu'il marche pour les replanifications et reformat code pour
#               aller plus vite
################################################################

###########################################
##### SCRIPT SENO - ETAPE 1 : MEDECIN #####
###########################################

DEBUG = False
LOG_FILE = False

#########################################
##### VARIABLES GLOBALES RAYSTATION #####
#########################################

patient_db = get_current("PatientDB")
ui = get_current("ui")

##############################
##### VARIABLES GLOBALES #####
##############################

path_RS = r"\\PMS-RAY2-DB01\RS_Dicom"
Date_et_Heure = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
VersionScript = "1.2"
fichier_dictionnaire_annotate = r"\\PMS-RAY2-DB01\RS_Scripts\struc_seno.csv"

if LOG_FILE:
    saveout = sys.stdout
    print("saveout : ", saveout)
    filename = r"\\PMS-RAY2-DB01\RS_Scripts\logs\logs_" + datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".txt"
    print("filename log : ", filename)
    fsock = open(filename, 'w')
    sys.stdout = fsock


#############################
##### FONCTIONS DE CASE #####
#############################

def find_exam(case):
    """Fonction renvoyant :
            :None si pas de CT dans le Case
            :le nom du CT si un seul CT
            :la liste des noms des CTs si plusieurs CTs"""
    if case.Examinations.Count == 0:
        return None
    elif case.Examinations.Count == 1:
        return [case.Examinations[0].Name]
    else:
        liste_exam = [examination.Name for examination in case.Examinations]
        return liste_exam

####################################
##### FONCTIONS D IMPORTATIONS #####
####################################

def import_struct(caseName, total_results_series, path_series):
    patient = get_current("Patient")
    for results, path in zip(total_results_series, path_series):
        print(path)
        patient.ImportDataFromPath(Path=path, CaseName=caseName, SeriesOrInstances=results)
        all_files = [os.path.join(path, o) for o in os.listdir(path) if os.path.isfile(os.path.join(path, o))]
        print("all_files = ", all_files)

        if not DEBUG:
            for f in all_files:
                os.remove(f)
            os.rmdir(path)
    return

def return_rtstruct(path, patient_id, study_to_import):
    """Fonction renvoyant les RTstruct et les chemins associé si plusieurs séries à importer """
    # Récupération du patient ID (key) et study Instance ID (value) dans list_study_to_import
    # UNE SEULE study_to_import POSSIBLE DONC PAS BESOIN DE FAIRE UNE LISTE
    # TOUTE LA FONCTION EST A MODIFIER CAR ELLE PREND EN COMPTE LE FAIT QU'ON PEUT RECUPERER PLUSIEURS SERIES
    list_study_to_import = []
    list_study_to_import.append({'PatientID': patient_id, 'StudyInstanceUID': study_to_import})

    # Récupère les chemins de tous les dossiers contenue dans le serveur \\PMS-RAY2-DB01\RS_Dicom
    all_path = [os.path.join(path, o) for o in os.listdir(path) if
                (os.path.isdir(os.path.join(path, o)) and "ARTPLAN" in o)]
    total_results_series = []
    path_series = []
    for study_to_import in list_study_to_import:
        for path in all_path:
            # Récupère le RTStruct du chemin concerné par ce tour de boucle seulement si le SearchCriterias correspond
            # à study_to_import
            series_to_import = [s for s in patient_db.QuerySeriesFromPath(Path=path, SearchCriterias=study_to_import) if
                                s['Modality'] == "RTSTRUCT"]
            if (series_to_import):
                path_series.append(path)
                results_series = []
                # Si le searchCriteria correspond, récupère l'ID du patient, le study instance uid et la série instance
                # uid dans results_series
                for result in series_to_import:
                    results_series.append({'PatientID': patient_id, 'StudyInstanceUID': result['StudyInstanceUID'],
                                           'SeriesInstanceUID': result['SeriesInstanceUID']})
                total_results_series.append(results_series)

    if total_results_series:
        # renvoit tous les RTstruct et les chemins (si plusieurs MAIS NE DEVRAIT PAS ARRIVER)
        return [total_results_series, path_series]
    else:
        return [False, False]


class main_window():

    def annulation(self):
        """Si l'utilisateur clique sur "Annuler" dans la pop up -> quitte le script"""
        if LOG_FILE:
            sys.stdout = saveout
            fsock.close()
        sys.exit()

    def verif_radiobutton(self):
        """Fonction vérifiant que toutes les informations nécessaires au script ont été renseigénes dans la pop up:
        :technique de traitement
        :paroi/sein dans le cas unilat
        :paroi/sein pour les 2 côté dans le cas bilat
        Si toutes les informations sont renseignées -> lance la fonction create_struct()"""
        if self.listvariable_exam.get() == "":
            tkinter.messagebox.showerror("Erreur", "Choisir CT à contourer")
            return False
        if self.var3DVMAT.get() == " ":
            tkinter.messagebox.showerror("Erreur", "Choisir la technique de traitement")
            return False
        if self.varBilat.get() == "unilat":
            if self.varSein_unilat.get() == " ":
                tkinter.messagebox.showerror("Erreur", "Sélectionner paroi ou sein et la latéralité")
                return False
            else:
                self.create_struct()
                return True

        elif self.varBilat.get() == "bilat":
            if self.varSeinG_bilat.get() == " " or self.varSeinD_bilat.get() == " ":
                tkinter.messagebox.showerror("Erreur", "Sélectionner paroi ou sein pour les 2 côtés")
                return False
            else:
                self.create_struct()
                return True

        else:
            tkinter.messagebox.showerror("Erreur", "Choisir si traitement unilatéral ou bilatéral")
            return False

    def create_struct(self):
        """Fonction qui :
                :récupère un dictionnaire associant noms français et anglais des ROIs en fonction des choix faits par
                l'utilisateur dans la pop up
                :crée un dictionnaire associant noms anglais des ROIs et leur caractéristiques
                :récupère le 1er CT
                :"""

        # Peut être mettre la fonction en dehors de la class main_window pour plus de clarté ?
        def charge_dict_roi(self):
            """Fonction renvoyant un dictionnaire associant les noms français des ROIs (Annotate) et les noms anglais
            des ROIs (RS) ajustés en fonction des informations rentrées dans la pop up (+ courbe CT A ENLEVER)"""

            # Ouverture du fichier .csv contenant la correspondance entre noms des ROIS français Annotate et  anglais RS
            file = open(fichier_dictionnaire_annotate, "r")
            lines = file.readlines()
            file.close()

            dict_roi = {}  # dictionnaire de correspondance entre nom des ROIs anglais et français

            for line in lines:
                if line.split(';')[0].strip() == "###":
                    pass

                # Lorsque le script lit la ligne commençant par "###SCAN" :
                # Récupération de la courbe du scanner GOSIM dans le fichier excel, A ENLEVER
                elif line.split(';')[0].strip() == "###SCAN":
                    str_courbe_CT2ED = line.split(';')[1].strip()
                    if DEBUG:
                        Patient = get_current("Patient")
                        Patient.Save()
                        if (str(Patient.ModificationInfo.SoftwareVersion) == '7.99.3.2'):
                            str_courbe_CT2ED = "SiemensIGR_ssTi"

                # Lorsque le script lit la ligne qui commence par "####EOF" = dernière ligne du fichier .csv :
                # Ajouts des noms des CTV français et de leur correspondant anglais au dictionnaire en fonction des
                # choix fait par l'utilisateur dans la pop up
                # SCRIPT FAIT CETTE ACTION EN DERNIER, A METTRE A LA FIN DE LA FONCTION charge_dict_roi()
                elif line.split(';')[0].strip() == "###EOF":
                    if self.varBilat.get() == "bilat":
                        if self.varSeinD_bilat.get() == "paroiD_bilat":
                            dict_roi['Sein D'] = "CTVp_thoracicw_R_skin"
                        if self.varSeinG_bilat.get() == "paroiG_bilat":
                            dict_roi['Sein G'] = "CTVp_thoracicw_L_skin"
                    if self.varBilat.get() == "unilat" and (self.varSein_unilat.get() == "paroiD_unilat"):
                        dict_roi['Sein D'] = "CTVp_thoracicw_skin"
                    if self.varBilat.get() == "unilat" and (self.varSein_unilat.get() == "paroiG_unilat"):
                        dict_roi['Sein G'] = "CTVp_thoracicw_skin"

                    return dict_roi, str_courbe_CT2ED

                else:
                    # Toutes les structures du fichier .csv dont la ligne est lu mais qui ne seront pas utilisées du fait
                    # des choix de l'utilisateur dans la pop up auront une value "None" (voir .csv)
                    # Pour la ligne lu par le script :
                    # Si l'utilisateur a choisi bilat, ajout des noms des ROIs français d'Annotate en keys (1e colonne
                    # du .csv) et des noms des ROIs anglais RS en value (2e colonne pour bilat)
                    if self.varBilat.get() == "bilat":
                        dict_roi[line.split(';')[0].strip()] = line.split(';')[1].strip()

                    # Si l'utilisateur a choisi unilat et côté droit, ajout des noms des ROIs français d'Annotate en
                    # keys (1e colonne du .csv) et des noms des ROIs anglais RS en value (3e colonne pour unilat droit)
                    if self.varBilat.get() == "unilat" and (
                            self.varSein_unilat.get() == "seinD_unilat" or self.varSein_unilat.get() == "paroiD_unilat"):
                        dict_roi[line.split(';')[0].strip()] = line.split(';')[2].strip()

                    # Si l'utilisateur a choisi unilat et côté gauche, ajout des noms des ROIs français d'Annotate en
                    # keys (1e colonne du .csv) et des noms des ROIs anglais RS en value (4e colonne pour unilat gauche)
                    if self.varBilat.get() == "unilat" and (
                            self.varSein_unilat.get() == "seinG_unilat" or self.varSein_unilat.get() == "paroiG_unilat"):
                        dict_roi[line.split(';')[0].strip()] = line.split(';')[3].strip()

        self.top.withdraw()

        dict_roi, str_courbe_CT2ED = charge_dict_roi(self)

        # Création d'un dictionnaire associant les noms anglais de ROI (keys) aux caractéristiques de la ROI (type,
        # couleur, booléen) rentrées en values

        ROI_list = {}

        ROI_list["Heart"] = ["Organ", "255,84,255", True]
        ROI_list["Spinal_cord"] = ["Organ", "255,128,64", True]
        ROI_list["External"] = ["External", "0,128,0", True]
        ROI_list["Larynx"] = ["Organ", "255,128,64", True]
        ROI_list["Liver"] = ["Organ", "128,64,64", True]
        ROI_list["Stomach"] = ["Organ", "128,128,0", True]
        ROI_list["Thyroid"] = ["Organ", "128,128,255", True]
        ROI_list["Esophagus"] = ["Organ", "64,0,0", True]

        if self.varBilat.get() == "unilat":
            ROI_list["Lung_ipsilat"] = ["Organ", "0,170,0", True]
            ROI_list["Lung_contra"] = ["Organ", "0,84,255", True]
            ROI_list["Breast_contra"] = ["Organ", "255,0,255", True]
            ROI_list["HumeralHead"] = ["Organ", "0,255,128", True]

            # Il faudrait vérifier ici que les GG ne sont pas des cibles avant de les créer (évite d'avoir à les supp après)
            ROI_list["CTVn_IMN"] = ["CTV", "0,255,0", False]
            ROI_list["CTVn_interpec"] = ["CTV", "255,165,0", False]
            ROI_list["CTVn_L1"] = ["CTV", "255,128,64", False]
            ROI_list["CTVn_L2"] = ["CTV", "170,0,126", False]
            ROI_list["CTVn_L3"] = ["CTV", "243,199,118", False]
            ROI_list["CTVn_L4"] = ["CTV", "83,66,34", False]

            # Intégration du plexus brachial au dictionnaire si un/des GG a/ont été coché(s) dans la pop up
            if self.int_gg_IMN.get() or self.int_gg_L1.get() or self.int_gg_L2.get() or self.int_gg_L3.get() \
                    or self.int_gg_L4.get() or self.int_gg_interpec.get():
                ROI_list["BrachialPlexus"] = ["Organ", "128,255,0", True]

            if (self.varSein_unilat.get() == "seinG_unilat" or self.varSein_unilat.get() == "seinD_unilat"):
                ROI_list["CTVp_breast_skin"] = ["CTV", "128,64,64", True]
                ROI_list["CTVp_tumourbed"] = ["CTV", "139,69,19", False]

            if (self.varSein_unilat.get() == "paroiG_unilat" or self.varSein_unilat.get() == "paroiD_unilat"):
                ROI_list["CTVp_thoracicw_skin"] = ["CTV", "128,64,0", True]
                ROI_list["Scar"] = ["IrradiatedVolume", "255,0,0", True]

        if self.varBilat.get() == "bilat":
            ROI_list["Lung_R"] = ["Organ", "0,170,0", True]
            ROI_list["Lung_L"] = ["Organ", "0,84,255", True]
            ROI_list["HumeralHead_R"] = ["Organ", "0,255,255", True]
            ROI_list["HumeralHead_L"] = ["Organ", "0,255,128", True]

            ROI_list["CTVn_IMN_L"] = ["CTV", "0,255,0", False]
            ROI_list["CTVn_interpec_L"] = ["CTV", "0,0,255", False]
            ROI_list["CTVn_L1_L"] = ["CTV", "255,128,64", False]
            ROI_list["CTVn_L2_L"] = ["CTV", "170,0,126", False]
            ROI_list["CTVn_L3_L"] = ["CTV", "243,199,118", False]
            ROI_list["CTVn_L4_L"] = ["CTV", "83,66,34", False]
            ROI_list["CTVn_IMN_R"] = ["CTV", "0,255,255", False]
            ROI_list["CTVn_interpec_R"] = ["CTV", "0,255,255", False]
            ROI_list["CTVn_L1_R"] = ["CTV", "139,69,19", False]
            ROI_list["CTVn_L2_R"] = ["CTV", "0,0,255", False]
            ROI_list["CTVn_L3_R"] = ["CTV", "255,165,0", False]
            ROI_list["CTVn_L4_R"] = ["CTV", "0,255,255", False]

            if self.varSeinG_bilat.get() == "seinG_bilat":
                ROI_list["CTVp_breast_L_skin"] = ["CTV", "128,64,64", True]
                ROI_list["CTVp_tumourbed_L"] = ["CTV", "139,69,19", False]
            if self.varSeinG_bilat.get() == "paroiG_bilat":
                ROI_list["CTVp_thoracicw_L_skin"] = ["CTV", "255,0,0", True]
                ROI_list["Scar_L"] = ["IrradiatedVolume", "255,0,0", True]
            if self.varSeinD_bilat.get() == "seinD_bilat":
                ROI_list["CTVp_breast_R_skin"] = ["CTV", "139,69,19", True]
                ROI_list["CTVp_tumourbed_R"] = ["CTV", "255,255,0", False]
            if self.varSeinD_bilat.get() == "paroiD_bilat":
                ROI_list["CTVp_thoracicw_R_skin"] = ["CTV", "0,128,0", True]
                ROI_list["Scar_R"] = ["IrradiatedVolume", "255,192,203", True]

            if self.int_gg_IMN.get() or self.int_gg_L1.get() or self.int_gg_L2.get() or self.int_gg_L3.get() \
                    or self.int_gg_L4.get() or self.int_gg_interpec.get():
                ROI_list["BrachialPlexus_R"] = ["Organ", "255,0,255", True]
            if self.int_gg_IMN2.get() or self.int_gg_L12.get() or self.int_gg_L22.get() or self.int_gg_L32.get() \
                    or self.int_gg_L42.get() or self.int_gg_interpec2.get():
                ROI_list["BrachialPlexus_L"] = ["Organ", "128,255,0", True]

        # Case et patient déjà récupérer dans init -> A METTRE EN ARGUMENTS ?
        Case = get_current("Case")
        Patient = get_current("Patient")

        # Récupération de la liste de nom des CTs
        exam_list = find_exam(Case)
        # Si plusieurs noms on récupère celui que l'utilisateur a choisi
        if len(exam_list) > 1:
            exam = self.listvariable_exam.get()
            print('exam récupéré : ', exam)
        # Si un seul CT on le récupère
        if len(exam_list) == 1:
            exam = exam_list[0]
        # Si pas de CT, message d'erreur
        if len(exam_list) == 0:
            tkinter.messagebox.showerror("Erreur", f"Pas d'examen disponible dans Raystation !")
            if LOG_FILE:
                sys.stdout = saveout
                fsock.close()
            sys.exit()

        # Avant d'importer on récupère la liste des ROIs présentent initialement dans le case (dans le cas d'une replanif
        # par exemple)
        global initial_rois_in_case
        initial_rois_in_case = [roi.Name for roi in Case.PatientModel.RegionsOfInterest]
        # Récupère le study instance UID du CT choisi
        study_to_import = Case.Examinations[exam].GetAcquisitionDataFromDicom()['StudyModule']['StudyInstanceUID']

        # Récupère tous les RTstruct (si plusieurs mais ne devrait pas arriver?) et leur chemin associés
        total_results_series, path_series = return_rtstruct(path_RS, Patient.PatientID, study_to_import)

        # Si aucun RT struct avec study instance uid n'a été trouvé -> message d'erreur
        if not total_results_series:
            if not (tkinter.messagebox.askokcancel("Avertissement",
                                                   "Aucune structure dicom trouvée !\nAucun contours Annotate ne sera "
                                                   "importé.\nCliquer sur OK pour continuer, Cancel pour arrêter")):
                if LOG_FILE:
                    sys.stdout = saveout
                    fsock.close()
                sys.exit()

        else:
            # On enregistre avant d'importer (obligatoire) et on importe RT struct
            Patient.Save()
            import_struct(Case.CaseName, total_results_series, path_series)

        # Récupération de toutes les ROIs dans RS = toutes les ROIs de Annotate si pas de replanif A MODIFIER
        total_roi_Annotate = [roi.Name for roi in Case.PatientModel.RegionsOfInterest]
        buf_total_roi_Annotate = copy.deepcopy(total_roi_Annotate)
        patient_model = Case.PatientModel
        for key in dict_roi:
            if key in total_roi_Annotate:
                # Cas ou le nom de la roi existe déjà dans la liste des rois présentes avant importation (=replanif)
                if dict_roi[key] not in initial_rois_in_case:
                    # Si ROI pas cochée par utilisateur ou pas dans la liste des ROIs qu'on contoure => on la supprime
                    if dict_roi[key] == "none" or not dict_roi[key] in ROI_list:
                        patient_model.RegionsOfInterest[key].DeleteRoi()
                        buf_total_roi_Annotate.remove(key)
                    # Si elle est cochée ou nécessaire on change son nom et on lui met le bon organtype
                    else:
                        patient_model.RegionsOfInterest[key].Name = dict_roi[key]
                        buf_total_roi_Annotate[buf_total_roi_Annotate.index(key)] = dict_roi[key]

                        patient_model.RegionsOfInterest[dict_roi[key]].Type = ROI_list[dict_roi[key]][0]
                        if ROI_list[dict_roi[key]][0] == 'CTV':
                            patient_model.RegionsOfInterest[dict_roi[key]].OrganData.OrganType = "Target"
                        if ROI_list[dict_roi[key]][0] == 'Organ':
                            patient_model.RegionsOfInterest[dict_roi[key]].OrganData.OrganType = "OrganAtRisk"
                        if ROI_list[dict_roi[key]][0] == 'IrradiatedVolume':
                            patient_model.RegionsOfInterest[dict_roi[key]].OrganData.OrganType = "Target"
                        if ROI_list[dict_roi[key]][0] == 'Undefined':
                            patient_model.RegionsOfInterest[dict_roi[key]].OrganData.OrganType = "Other"
                        patient_model.RegionsOfInterest[dict_roi[key]].Color = ROI_list[dict_roi[key]][1]
                # Cas ou le nom de la roi n'existe pas déjà dans la liste des rois présentes avant importation
                else:
                    # Si la n'est pas cochée par utilisateur ou pas dans la liste des ROIs qu'on contoure on ne fait rien
                    if dict_roi[key] == "none" or not dict_roi[key] in ROI_list:
                        pass
                    # Si elle est cochée ou nécessaire, on copie sa géom dans la roi pré-existante du nom corresp anglais
                    # et on supp la ROI au nom fr
                    else:
                        patient_model.RegionsOfInterest[dict_roi[key]].CreateAlgebraGeometry(
                            Examination=Case.Examinations[exam], Algorithm="Auto",
                            ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [key], 'MarginSettings': {
                                'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0,
                                    'Right': 0, 'Left': 0}},
                            ExpressionB={'Operation': "Union", 'SourceRoiNames': [], 'MarginSettings': {
                                'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0,
                                    'Right': 0, 'Left': 0}},
                            ResultOperation="None",
                            ResultMarginSettings={'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0,
                                'Posterior': 0, 'Right': 0, 'Left': 0})
                        # On supprime la ROI au nom français SAUF pour larynx car c'est le même nom qu'en anglais
                        # (seul ROI dans ce cas)
                        if key != 'Larynx':
                            patient_model.RegionsOfInterest[key].DeleteRoi()
                            buf_total_roi_Annotate.remove(key)
        total_roi_Annotate = copy.deepcopy(buf_total_roi_Annotate)
        buf_total_roi_Annotate = []

        buf_total_roi_Annotate = copy.deepcopy(total_roi_Annotate)
        # On supprime toutes les structures dans RS qui ne sont pas dans les struct prévues pour ce cas (ROI_list)
        for roi in total_roi_Annotate:
            if not roi in ROI_list and not roi in initial_rois_in_case:
                patient_model.RegionsOfInterest[roi].DeleteRoi()
                buf_total_roi_Annotate.remove(roi)
        total_roi_Annotate = copy.deepcopy(buf_total_roi_Annotate)
        buf_total_roi_Annotate = []

        roi_dict = patient_model.RegionsOfInterest
        # S'il reste des ROIs de la list prévue (ROI_list) qui ne sont pas créées dans RS on les crée
        for name, [type, color, mandatory] in ROI_list.items():
            if not name in total_roi_Annotate and not name in initial_rois_in_case:
                roi_list_name = [roi.Name for roi in Case.PatientModel.RegionsOfInterest]
                patient_model.CreateRoi(Name=name, Color=color, Type=type, TissueName=None, RbeCellTypeName=None,
                                            RoiMaterial=None)

        # Création du contour externe
        # if 'External' not in initial_rois_in_case:
        #     Case.PatientModel.CreateRoi(Name='External', Color=color, Type=type, TissueName=None, RbeCellTypeName=None,
        #                                     RoiMaterial=None)
        roi_dict["External"].CreateExternalGeometry(Examination=Case.Examinations[exam])
        if "Scar" in ROI_list.keys():
                if "Scar" not in  initial_rois_in_case:
                    roi_dict["Scar"].OrganData.OrganType = "Target"
        if "Scar_L" in ROI_list.keys():
            if "Scar_L" not in initial_rois_in_case:
                roi_dict["Scar_L"].OrganData.OrganType = "Target"
        if "Scar_R" in ROI_list.keys():
            if "Scar_R" not in initial_rois_in_case:
                roi_dict["Scar_R"].OrganData.OrganType = "Target"

        # On supprime les CTVn s'ils n'ont pas été sélectionnés par l'utilisateur dans le pop up

        if self.varBilat.get() == "unilat":

            if not self.int_gg_IMN.get():
                del ROI_list["CTVn_IMN"]
                if not 'CTVn_IMN' in initial_rois_in_case:
                    roi_dict["CTVn_IMN"].DeleteRoi()
            if not self.int_gg_interpec.get():
                del ROI_list["CTVn_interpec"]
                if not 'CTVn_interpec' in initial_rois_in_case:
                    roi_dict["CTVn_interpec"].DeleteRoi()
            if not self.int_gg_L1.get():
                del ROI_list["CTVn_L1"]
                if not 'CTVn_L1' in initial_rois_in_case:
                    roi_dict["CTVn_L1"].DeleteRoi()
            if not self.int_gg_L2.get():
                del ROI_list["CTVn_L2"]
                if not 'CTVn_L2' in initial_rois_in_case:
                    roi_dict["CTVn_L2"].DeleteRoi()
            if not self.int_gg_L3.get():
                del ROI_list["CTVn_L3"]
                if not 'CTVn_L3' in initial_rois_in_case:
                    roi_dict["CTVn_L3"].DeleteRoi()
            if not self.int_gg_L4.get():
                del ROI_list["CTVn_L4"]
                if not 'CTVn_L4' in initial_rois_in_case:
                    roi_dict["CTVn_L4"].DeleteRoi()

        if self.varBilat.get() == "bilat":

            if not self.int_gg_IMN.get():
                del ROI_list["CTVn_IMN_R"]
                if not 'CTVn_IMN_R' in initial_rois_in_case:
                    roi_dict["CTVn_IMN_R"].DeleteRoi()
            if not self.int_gg_interpec.get():
                del ROI_list["CTVn_interpec_R"]
                if not 'CTVn_interpec_R' in initial_rois_in_case:
                    roi_dict["CTVn_interpec_R"].DeleteRoi()
            if not self.int_gg_L1.get():
                del ROI_list["CTVn_L1_R"]
                if not 'CTVn_L1_R' in initial_rois_in_case:
                    roi_dict["CTVn_L1_R"].DeleteRoi()
            if not self.int_gg_L2.get():
                del ROI_list["CTVn_L2_R"]
                if not 'CTVn_L2_R' in initial_rois_in_case:
                    roi_dict["CTVn_L2_R"].DeleteRoi()
            if not self.int_gg_L3.get():
                del ROI_list["CTVn_L3_R"]
                if not 'CTVn_L3_R' in initial_rois_in_case:
                    roi_dict["CTVn_L3_R"].DeleteRoi()
            if not self.int_gg_L4.get():
                del ROI_list["CTVn_L4_R"]
                if not 'CTVn_L4_R' in initial_rois_in_case:
                    roi_dict["CTVn_L4_R"].DeleteRoi()

            if not self.int_gg_IMN2.get():
                del ROI_list["CTVn_IMN_L"]
                if not 'CTVn_IMN_L' in initial_rois_in_case:
                    roi_dict["CTVn_IMN_L"].DeleteRoi()
            if not self.int_gg_interpec2.get():
                del ROI_list["CTVn_interpec_L"]
                if not 'CTVn_interpec_L' in initial_rois_in_case:
                    roi_dict["CTVn_interpec_L"].DeleteRoi()
            if not self.int_gg_L12.get():
                del ROI_list["CTVn_L1_L"]
                if not 'CTVn_L1_L' in initial_rois_in_case:
                    roi_dict["CTVn_L1_L"].DeleteRoi()
            if not self.int_gg_L22.get():
                del ROI_list["CTVn_L2_L"]
                if not 'CTVn_L2_L' in initial_rois_in_case:
                    roi_dict["CTVn_L2_L"].DeleteRoi()
            if not self.int_gg_L32.get():
                del ROI_list["CTVn_L3_L"]
                if not 'CTVn_L3_L' in initial_rois_in_case:
                    roi_dict["CTVn_L3_L"].DeleteRoi()
            if not self.int_gg_L42.get():
                del ROI_list["CTVn_L4_L"]
                if not 'CTVn_L4_L' in initial_rois_in_case:
                    roi_dict["CTVn_L4_L"].DeleteRoi()

        Patient.Save()

        self.create_PTV_and_dosi_ROI(Case, exam, [[name, type, color, mandatory] for name, [type, color, mandatory] in
                                                  ROI_list.items()], initial_rois_in_case)
        roi_dict_str_set = Case.PatientModel.StructureSets[exam].RoiGeometries

        # Pop up indiquant les ROIs créées n'ayant pas de contours et demander de réaliser les contours à l'utilisateur
        phrase = ""
        for name, [type, color, mandatory] in ROI_list.items():
            if not roi_dict_str_set[name].HasContours():
                phrase = phrase + f"{name} {'(obligatoire)' if ROI_list[name][2] else ''}" + "\n"  #

        tkinter.messagebox.showinfo("Information",
                                    "Vérifier les contours automatiques et réaliser les contours :\n" + phrase)

        caseName = [c.CaseName for c in Patient.Cases]
        # # Récupère le nom du dernier case créé MAIS SERT A RIEN JE CROIS, A VERIFIER
        caseName.pop()

        # Compte le nombre de case
        i = len(caseName) + 1
        new_caseName = f"Case"
        inc_temp_name = new_caseName + f" {i}"
        # Vérifie qu'il n'existe pas déjà un Case avec le nom "Case X" avec X = nombre de case
        if (new_caseName + f" {i}") in ''.join(caseName):
            while inc_temp_name in ''.join(caseName):
                inc_temp_name = new_caseName + f" {i}"
                i = i + 1

        # Renomme le patient avec le bon numéro de case et define le body site
        Case.CaseName = inc_temp_name
        self.define_body_site(Case)
        Patient.Save()
        if LOG_FILE:
            sys.stdout = saveout
            fsock.close()

        # Clique sur les onlgets de RS de manière à se mettre sur Structure Definition
        ui.TitleBar.Navigation.MenuItem[3].Click()
        ui.TitleBar.Navigation.MenuItem[3].Popup.MenuItem[1].Click()
        # ui.TitleBar.Navigation.MenuItem['Patient Modeling'].Popup.MenuItem["Structure Definition"].Click()
        ui.ToolPanel.TabItem['ROIs'].Select()

        sys.exit()

    # FONCTION A METTRE AILLEURS
    def define_body_site(self, Case):
        """ Fonctions définissant le body site correspondant aux informations renseignées par l'utilisateur dans la
        pop up dans RS"""
        if self.varBilat.get() == "unilat":
            if self.var3DVMAT.get() == "3D":
                if self.varSein_unilat.get() == "paroiG_unilat" or self.varSein_unilat.get() == "seinG_unilat":
                    Case.BodySite = (f"SEIN-PAROI+/-GG G - RC3D")
                else:
                    Case.BodySite = (f"SEIN-PAROI+/-GG D - RC3D")

            if self.var3DVMAT.get() == "TOMO":
                if self.varSein_unilat.get() == "paroiG_unilat" or self.varSein_unilat.get() == "seinG_unilat":
                    Case.BodySite = (f"SEIN-PAROI+/-GG G - TOMO")
                else:
                    Case.BodySite = (f"SEIN-PAROI+/-GG D - TOMO")

            if self.var3DVMAT.get() == "VMAT":
                if self.varSein_unilat.get() == "paroiG_unilat" or self.varSein_unilat.get() == "seinG_unilat":
                    Case.BodySite = (f"SEIN-PAROI+/-GG G - VMAT")
                else:
                    Case.BodySite = (f"SEIN-PAROI+/-GG D - VMAT")

            if self.var3DVMAT.get() == "IMRT":
                if self.varSein_unilat.get() == "paroiG_unilat" or self.varSein_unilat.get() == "seinG_unilat":
                    Case.BodySite = (f"SEIN-PAROI+/-GG G - IMRT")
                else:
                    Case.BodySite = (f"SEIN-PAROI+/-GG D - IMRT")

        if self.varBilat.get() == "bilat":
            if self.var3DVMAT.get() == "3D":
                Case.BodySite = (f"SEIN-PAROI+/-GG BILAT - RC3D")
            if self.var3DVMAT.get() == "TOMO":
                Case.BodySite = (f"SEIN-PAROI+/-GG BILAT - TOMO")
            if self.var3DVMAT.get() == "VMAT":
                Case.BodySite = (f"SEIN-PAROI+/-GG BILAT - VMAT")
            if self.var3DVMAT.get() == "IMRT":
                Case.BodySite = (f"SEIN-PAROI+/-GG BILAT - IMRT")

    # Fonction à mettre avant (hors de la main window ou dedans plus haut)
    def create_PTV_and_dosi_ROI(self, Case, exam, roi_list, initial_rois_in_case):
        """Fonction créant les volumes suivants :
            :Lungs
            :CTVp_breast/CTVp_breast_R et CTVp_breast_L/CTVp_thoracicw/CTVp_thoracicw_R et CTVp_thoracicw_L
            :PTVp_breast/PTVp_breast_R et PTVp_breast_L/PTVp_thoracicw/PTVp_thoracicw_L et PTVp_thoracicw_R
            :PTVp_tumourbed/PTVp_tumourbed_R et PTVp_tumourbed_L
            :CTVn_Ltot/CTVn_Ltot_R et CTVn_Ltot_L
            :PTVn_Ltot/PTVn_Ltot_R et PTVn_Ltot_L
            :PTVn_IMN/PTVn_IMN_L et PTVn_IMN_R
            :PTV TOT"""
        roi_dict = Case.PatientModel.RegionsOfInterest
        patient_model = Case.PatientModel
        def set_algebra(roi_dict, expression_a, expression_b, result_operation, margin_a, margin_b, margin_result,
                        resulting_roi_name):
            ExpressionA = {'Operation': "Union", 'SourceRoiNames': expression_a,
                           'MarginSettings': {'Type': "Expand", 'Superior': margin_a, 'Inferior': margin_a,
                                              'Anterior': margin_a,
                                              'Posterior': margin_a, 'Right': margin_a, 'Left': margin_a}}
            ExpressionB = {'Operation': "Union", 'SourceRoiNames': expression_b,
                           'MarginSettings': {'Type': "Contract", 'Superior': margin_b, 'Inferior': margin_b,
                                              'Anterior': margin_b,
                                              'Posterior': margin_b, 'Right': margin_b, 'Left': margin_b}}
            ResultOperation = result_operation
            ResultMarginSettings = {'Type': "Contract", 'Superior': margin_result, 'Inferior': margin_result,
                                    'Anterior': margin_result,
                                    'Posterior': margin_result, 'Right': margin_result, 'Left': margin_result}
            roi_dict[resulting_roi_name].SetAlgebraExpression(ExpressionA=ExpressionA, ExpressionB=ExpressionB,
                                                              ResultOperation=ResultOperation,
                                                              ResultMarginSettings=ResultMarginSettings)
            return

        # Création du volume Lungs
        # S'il n'existe pas dans les ROIs présentes avant le lancement du script -> on le crée et on lui affecte une
        # géométrie
        if 'Lungs' not in initial_rois_in_case:
            patient_model.CreateRoi(Name="Lungs", Color="170,0,255", Type="Organ", TissueName=None,
                                        RbeCellTypeName=None, RoiMaterial=None)
            if self.varBilat.get() == "bilat":
                expression_a = ["Lung_R", "Lung_L"]
            else:
                expression_a = ["Lung_ipsilat", "Lung_contra"]

            set_algebra(roi_dict, expression_a, [], 'None', 0, 0, 0, 'Lungs')

        # S'il existe déjà dans les ROIs présentes av lancement du script (=replanif) on ne fait que  l'update en
        # faisant confiance que le booléen a bien été créé la première fois (on est obligé car les structures sont déjà
        # approuvées dans le cas d'une replanif et on ne peut pas les modifier dans cet état)
        roi_dict["Lungs"].UpdateDerivedGeometry(Examination=Case.Examinations[exam], Algorithm="Auto")

        # Création du volume CTVp_breast ou CTVp_thoracicw à partir du CTVp_breast_skin ou CTVp_thoracicw_skin

        dict_color = {"CTVp_breast_skin": "255,128,255", "CTVp_thoracicw_skin": "0,255,255",
                      "CTVp_breast_L_skin": "255,128,255", "CTVp_breast_R_skin": "0,255,255",
                      "CTVp_thoracicw_L_skin": "0,0,255", "CTVp_thoracicw_R_skin": "255,0,255"}

        for ctv_skin in [c for c in
                         ["CTVp_breast_skin", "CTVp_thoracicw_skin", "CTVp_breast_L_skin", "CTVp_breast_R_skin",
                          "CTVp_thoracicw_L_skin", "CTVp_thoracicw_R_skin"] if c in [r[0] for r in roi_list]]:
            if ctv_skin[:-5] not in initial_rois_in_case:
                patient_model.CreateRoi(Name=ctv_skin[:-5], Color=dict_color[ctv_skin], Type="CTV", TissueName=None,
                                            RbeCellTypeName=None, RoiMaterial=None)
                if ctv_skin[-6] == 'L':
                    marge = float(self.listvariable_margin2.get())
                else:
                    marge = float(self.listvariable_margin.get())
                set_algebra(roi_dict, [ctv_skin], ['External'], 'Intersection', 0, marge, 0, ctv_skin[:-5])
            roi_dict[ctv_skin[:-5]].UpdateDerivedGeometry(Examination=Case.Examinations[exam], Algorithm="Auto")

        if self.varBilat.get() == "unilat":
            # list PTV_tot servira à ajouter toutes les ROIs nécessaires à la construction de la ROI PTV TOT
            PTV_tot = []

            if self.varSein_unilat.get() == "seinG_unilat" or self.varSein_unilat.get() == "seinD_unilat":
                roiBreast = "CTVp_breast"
            else:
                roiBreast = "CTVp_thoracicw"

            # Création du PTV sein/paroi à partir du CTV sein/paroi
            ptv_name = "PTVp_" + roiBreast[5:]
            if ptv_name not in initial_rois_in_case:
                patient_model.CreateRoi(Name=ptv_name, Color="64,128,128", Type="PTV", TissueName=None,
                                            RbeCellTypeName=None, RoiMaterial=None)
                set_algebra(roi_dict, ["CTVp_" + roiBreast[5:]], ['External'], 'Intersection', 0.5,
                            float(self.listvariable_margin.get()), 0, ptv_name)
            PTV_tot.append("PTVp_" + roiBreast[5:])
            roi_dict[ptv_name].UpdateDerivedGeometry(Examination=Case.Examinations[exam], Algorithm="Auto")

            # Création du PTV boost à partir du CTV boost
            if "CTVp_tumourbed" in [r[0] for r in roi_list]:
                if 'PTVp_tumourbed' not in initial_rois_in_case:
                    patient_model.CreateRoi(Name="PTVp_tumourbed", Color="128,255,0", Type="PTV", TissueName=None,
                                                RbeCellTypeName=None, RoiMaterial=None)
                    set_algebra(roi_dict, ['CTVp_tumourbed'], ['PTVp_breast'], 'Intersection', 1, 0, 0,
                                'PTVp_tumourbed')
                roi_dict['PTVp_tumourbed'].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                   Algorithm="Auto")

            # Création de la ROI CTVn_Ltot
            # Recherche du nombre de GG à ajouter à la ROI
            roi_to_add = []
            if 'CTVn_L1' in [r[0] for r in roi_list]:
                roi_to_add.append("CTVn_L1")

            if 'CTVn_L2' in [r[0] for r in roi_list]:
                roi_to_add.append("CTVn_L2")

            if 'CTVn_L3' in [r[0] for r in roi_list]:
                roi_to_add.append("CTVn_L3")

            if 'CTVn_L4' in [r[0] for r in roi_list]:
                roi_to_add.append("CTVn_L4")

            if 'CTVn_interpec' in [r[0] for r in roi_list]:
                roi_to_add.append("CTVn_interpec")

            if (roi_to_add):
                if 'CTVn_Ltot' not in initial_rois_in_case:
                    patient_model.CreateRoi(Name="CTVn_Ltot", Color="170,0,126", Type="CTV", TissueName=None,
                                                RbeCellTypeName=None, RoiMaterial=None)
                    set_algebra(roi_dict, roi_to_add, [], 'None', 0, 0, 0, 'CTVn_Ltot')
                roi_dict['CTVn_Ltot'].UpdateDerivedGeometry(Examination=Case.Examinations[exam], Algorithm="Auto")
            # Création de la ROI PTVn_Ltot
                if 'PTVn_Ltot' not in initial_rois_in_case:
                    patient_model.CreateRoi(Name="PTVn_Ltot", Color="0,0,255", Type="PTV", TissueName=None,
                                                RbeCellTypeName=None, RoiMaterial=None)
                    set_algebra(roi_dict, ['CTVn_Ltot'], ['External'], 'Intersection', 0.5,
                                float(self.listvariable_margin.get()), 0, 'PTVn_Ltot')
                PTV_tot.append("PTVn_Ltot")
                roi_dict['PTVn_Ltot'].UpdateDerivedGeometry(Examination=Case.Examinations[exam], Algorithm="Auto")
            # Création de la ROI PTVn_IMN
            if 'CTVn_IMN' in [r[0] for r in roi_list]:
                if 'PTVn_IMN' not in initial_rois_in_case:
                    patient_model.CreateRoi(Name="PTVn_IMN", Color="128,255,255", Type="PTV", TissueName=None,
                                                RbeCellTypeName=None, RoiMaterial=None)
                    set_algebra(roi_dict, ['CTVn_IMN'], ['External'], 'Intersection', 0.5,
                                float(self.listvariable_margin.get()), 0, 'PTVn_IMN')
                roi_dict['PTVn_IMN'].UpdateDerivedGeometry(Examination=Case.Examinations[exam], Algorithm="Auto")
                PTV_tot.append("PTVn_IMN")

            # Création de la ROI PTV TOT
            if 'PTV TOT' not in initial_rois_in_case:
                patient_model.CreateRoi(Name="PTV TOT", Color="0,0,64", Type="PTV", TissueName=None,
                                            RbeCellTypeName=None, RoiMaterial=None)
                set_algebra(roi_dict, PTV_tot, [], 'None', 0, 0, 0, 'PTV TOT')
            roi_dict['PTV TOT'].UpdateDerivedGeometry(Examination=Case.Examinations[exam], Algorithm="Auto")

        if self.varBilat.get() == "bilat":
            PTV_tot = []

            # Création de la ROI PTVp_thoracicw_L
            if self.varSeinG_bilat.get() == "paroiG_bilat":
                if 'PTVp_thoracicw_L' not in initial_rois_in_case:
                    patient_model.CreateRoi(Name="PTVp_thoracicw_L", Color="0,0,128", Type="PTV", TissueName=None,
                                                RbeCellTypeName=None, RoiMaterial=None)
                    set_algebra(roi_dict, ['CTVp_thoracicw_L'], ['External'], 'Intersection', 0.5,
                                float(self.listvariable_margin2.get()), 0, 'PTVp_thoracicw_L')
                PTV_tot.append("PTVp_thoracicw_L")
                roi_dict['PTVp_thoracicw_L'].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                   Algorithm="Auto")

            # Création de la ROI CTVp_thoracicw_L
            if self.varSeinD_bilat.get() == "paroiD_bilat":
                if 'PTVp_thoracicw_R' not in initial_rois_in_case:
                    patient_model.CreateRoi(Name="PTVp_thoracicw_R", Color="0,0,255", Type="PTV", TissueName=None,
                                                RbeCellTypeName=None, RoiMaterial=None)
                    set_algebra(roi_dict, ['CTVp_thoracicw_R'], ['External'], 'Intersection', 0.5,
                                float(self.listvariable_margin.get()), 0, 'PTVp_thoracicw_R')
                PTV_tot.append("PTVp_thoracicw_R")
                roi_dict['PTVp_thoracicw_R'].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                   Algorithm="Auto")

            # Création de la ROI PTVp_breast_L
            if self.varSeinG_bilat.get() == "seinG_bilat":
                if 'PTVp_breast_L' not in initial_rois_in_case:
                    patient_model.CreateRoi(Name="PTVp_breast_L", Color="64,128,128", Type="PTV", TissueName=None,
                                                RbeCellTypeName=None, RoiMaterial=None)
                    set_algebra(roi_dict, ['CTVp_breast_L'], ['External'], 'Intersection', 0.5,
                                float(self.listvariable_margin2.get()), 0, 'PTVp_breast_L')
                PTV_tot.append("PTVp_breast_L")
                roi_dict['PTVp_breast_L'].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                   Algorithm="Auto")
                # Création de la ROI PTVp_tumourbed_L
                if "CTVp_tumourbed_L" in [r[0] for r in roi_list]:
                    if 'PTVp_tumourbed_L' not in initial_rois_in_case:
                        patient_model.CreateRoi(Name="PTVp_tumourbed_L", Color="128,255,0", Type="PTV", TissueName=None,
                                                    RbeCellTypeName=None, RoiMaterial=None)
                        set_algebra(roi_dict, ['CTVp_tumourbed_L'], ['PTVp_breast_L'], 'Intersection', 1, 0, 0,
                                    'PTVp_tumourbed_L')
                    roi_dict['PTVp_tumourbed_L'].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                    Algorithm="Auto")

            # Création de la ROI PTVp_breast_R
            if self.varSeinD_bilat.get() == "seinD_bilat":
                if 'PTVp_breast_R' not in initial_rois_in_case:
                    patient_model.CreateRoi(Name="PTVp_breast_R", Color="139,69,19", Type="PTV", TissueName=None,
                                                RbeCellTypeName=None, RoiMaterial=None)
                    set_algebra(roi_dict, ['CTVp_breast_R'], ['External'], 'Intersection', 0.5,
                                float(self.listvariable_margin.get()), 0, 'PTVp_breast_R')
                PTV_tot.append("PTVp_breast_R")
                roi_dict['PTVp_breast_R'].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                   Algorithm="Auto")

                # Création de la ROI PTVp_tumourbed_R
                if "CTVp_tumourbed_R" in [r[0] for r in roi_list]:
                    if  'PTVp_tumourbed_R' not in initial_rois_in_case:
                        patient_model.CreateRoi(Name="PTVp_tumourbed_R", Color="255,192,203", Type="PTV",
                                                    TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
                        set_algebra(roi_dict, ['CTVp_tumourbed_R'], ['PTVp_breast_R'], 'Intersection', 1, 0,
                                    0, 'PTVp_tumourbed_R')
                    roi_dict['PTVp_tumourbed_R'].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                    Algorithm="Auto")
            # Création de la ROI CTVn_Ltot_L
            # Recherche du nombre de GG à ajouter à la ROI à G
            roi_to_add = []
            if 'CTVn_L1_L' in [r[0] for r in roi_list]:
                roi_to_add.append("CTVn_L1_L")

            if 'CTVn_L2_L' in [r[0] for r in roi_list]:
                roi_to_add.append("CTVn_L2_L")

            if 'CTVn_L3_L' in [r[0] for r in roi_list]:
                roi_to_add.append("CTVn_L3_L")

            if 'CTVn_L4_L' in [r[0] for r in roi_list]:
                roi_to_add.append("CTVn_L4_L")

            if 'CTVn_interpec_L' in [r[0] for r in roi_list]:
                roi_to_add.append("CTVn_interpec_L")

            if (roi_to_add):
                if 'CTVn_Ltot_L' not in initial_rois_in_case:
                    patient_model.CreateRoi(Name="CTVn_Ltot_L", Color="170,0,126", Type="CTV", TissueName=None,
                                                                            RbeCellTypeName=None, RoiMaterial=None)
                    set_algebra(roi_dict, roi_to_add, [], 'None', 0, 0, 0, 'CTVn_Ltot_L')
                roi_dict['CTVn_Ltot_L'].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                                   Algorithm="Auto")
                if 'PTVn_Ltot_L' not in initial_rois_in_case:
                    patient_model.CreateRoi(Name="PTVn_Ltot_L", Color="170,0,126", Type="PTV", TissueName=None,
                                                RbeCellTypeName=None, RoiMaterial=None)
                    set_algebra(roi_dict, ['CTVn_Ltot_L'], [], 'None', 0.5, 0, 0, 'PTVn_Ltot_L')
                PTV_tot.append("PTVn_Ltot_L")
                roi_dict['PTVn_Ltot_L'].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                              Algorithm="Auto")

            # Création de la ROI PTVn_IMN_L
            if 'CTVn_IMN_L' in [r[0] for r in roi_list]:
                if 'PTVn_IMN_L' not in initial_rois_in_case:
                    patient_model.CreateRoi(Name="PTVn_IMN_L", Color="128,255,255", Type="PTV", TissueName=None,
                                                RbeCellTypeName=None, RoiMaterial=None)
                    set_algebra(roi_dict, ['CTVn_IMN_L'], [], 'None', 0.5, 0, 0, 'PTVn_IMN_L')
                PTV_tot.append("PTVn_IMN_L")
                roi_dict['PTVn_IMN_L'].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                              Algorithm="Auto")

            # Création de la ROI CTVn_Ltot_R
            # Recherche du nombre de GG à ajouter à la ROI à R
            roi_to_add = []
            if 'CTVn_L1_R' in [r[0] for r in roi_list]:
                roi_to_add.append("CTVn_L1_R")

            if 'CTVn_L2_R' in [r[0] for r in roi_list]:
                roi_to_add.append("CTVn_L2_R")

            if 'CTVn_L3_R' in [r[0] for r in roi_list]:
                roi_to_add.append("CTVn_L3_R")

            if 'CTVn_L4_R' in [r[0] for r in roi_list]:
                roi_to_add.append("CTVn_L4_R")

            if 'CTVn_interpec_R' in [r[0] for r in roi_list]:
                roi_to_add.append("CTVn_interpec_R")

            if (roi_to_add):
                if 'CTVn_Ltot_R' not in initial_rois_in_case:
                    patient_model.CreateRoi(Name="CTVn_Ltot_R", Color="255,0,255", Type="CTV", TissueName=None,
                                                RbeCellTypeName=None, RoiMaterial=None)
                    set_algebra(roi_dict, roi_to_add, [], 'None', 0, 0, 0, 'CTVn_Ltot_R')
                roi_dict['CTVn_Ltot_R'].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                             Algorithm="Auto")
                # Création de la ROI CTVn_Ltot_G
                if 'PTVn_Ltot_R' not in initial_rois_in_case:
                    patient_model.CreateRoi(Name="PTVn_Ltot_R", Color="0,128,0", Type="PTV", TissueName=None,
                                                RbeCellTypeName=None, RoiMaterial=None)
                    set_algebra(roi_dict, ['CTVn_Ltot_R'], [], 'None', 0.5, 0, 0, 'PTVn_Ltot_R')
                PTV_tot.append("PTVn_Ltot_R")
                roi_dict['PTVn_Ltot_R'].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                             Algorithm="Auto")

            if 'CTVn_IMN_R' in [r[0] for r in roi_list]:
                if 'PTVn_IMN_R' not in initial_rois_in_case:
                    patient_model.CreateRoi(Name="PTVn_IMN_R", Color="0,128,0", Type="PTV", TissueName=None,
                                                RbeCellTypeName=None, RoiMaterial=None)
                    set_algebra(roi_dict, ['CTVn_IMN_R'], [], 'None', 0.5, 0, 0, 'PTVn_IMN_R')
                PTV_tot.append("PTVn_IMN_R")
                roi_dict['PTVn_IMN_R'].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                              Algorithm="Auto")

            # Création de la ROI PTV TOT
            if 'PTV TOT' not in initial_rois_in_case:
                patient_model.CreateRoi(Name="PTV TOT", Color="0,0,64", Type="PTV", TissueName=None,
                                            RbeCellTypeName=None, RoiMaterial=None)
                set_algebra(roi_dict, PTV_tot, [], 'None', 0, 0, 0, 'PTV TOT')
            roi_dict['PTV TOT'].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                                        Algorithm="Auto")
        # Création de la ROI External - PTV TOT
        if 'External - PTV TOT' not in initial_rois_in_case:
            patient_model.CreateRoi(Name=r"External - PTV TOT", Color="Yellow", Type="Undefined",
                                        TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
            set_algebra(roi_dict, ['External'], ['PTV TOT'], 'Subtraction', 0, 0, 0, 'External - PTV TOT')
        roi_dict['External - PTV TOT'].UpdateDerivedGeometry(Examination=Case.Examinations[exam],
                                          Algorithm="Auto")
    def verif_has_contours(self, Case, ROI_list, exam):
        for roi in ROI_list:
            if not Case.PatientModel.StructureSets[exam].RoiGeometries[roi[0]].HasContours() and roi[3]:
                tkinter.messagebox.showerror("Erreur", f"Le contours {roi[0]} est obligatoire !")
                return False
        return True

    def onClickRadio(self):
        """Fonction modifiant la marge par défaut du/des menus déroulants (selon si unilat ou bilat) en fonction de la
        technique"""
        if self.var3DVMAT.get() == "3D":
            self.OptionMenuMargin["menu"].delete(0, "end")
            self.OptionMenuMargin2["menu"].delete(0, "end")
            margin_list = ["0.3", "0.5"]
            margin_list2 = ["0.3", "0.5"]
            self.listvariable_margin.set(margin_list[1])
            self.listvariable_margin2.set(margin_list2[1])
            for value, value2 in zip(margin_list, margin_list2):
                self.OptionMenuMargin["menu"].add_command(label=value,
                                                          command=lambda v=value: self.listvariable_margin.set(v))
                self.OptionMenuMargin2["menu"].add_command(label=value2,
                                                           command=lambda v=value2: self.listvariable_margin2.set(v))

        if self.var3DVMAT.get() == "VMAT":
            self.OptionMenuMargin["menu"].delete(0, "end")
            self.OptionMenuMargin2["menu"].delete(0, "end")
            margin_list = ["0.1", "0.2", "0.3", "0.4", "0.5"]
            margin_list2 = ["0.1", "0.2", "0.3", "0.4", "0.5"]
            self.listvariable_margin.set(margin_list[2])
            self.listvariable_margin2.set(margin_list2[2])
            for value, value2 in zip(margin_list, margin_list2):
                self.OptionMenuMargin["menu"].add_command(label=value,
                                                          command=lambda v=value: self.listvariable_margin.set(v))
                self.OptionMenuMargin2["menu"].add_command(label=value2,
                                                           command=lambda v=value2: self.listvariable_margin2.set(v))

        if self.var3DVMAT.get() == "TOMO":
            self.OptionMenuMargin["menu"].delete(0, "end")
            self.OptionMenuMargin2["menu"].delete(0, "end")
            margin_list = ["0.1", "0.2", "0.3", "0.4", "0.5"]
            margin_list2 = ["0.1", "0.2", "0.3", "0.4", "0.5"]
            self.listvariable_margin.set(margin_list[2])
            self.listvariable_margin2.set(margin_list2[2])
            for value, value2 in zip(margin_list, margin_list2):
                self.OptionMenuMargin["menu"].add_command(label=value,
                                                          command=lambda v=value: self.listvariable_margin.set(v))
                self.OptionMenuMargin2["menu"].add_command(label=value2,
                                                           command=lambda v=value2: self.listvariable_margin2.set(v))

    def set_unilat(self):
        """ Fonction enlevant les radiobuttons et checkbuttons non utiles quand on selectionne unilat :
        :radiobuttons sein droit bi, paroi droite bi, sein gauche bi et paroi gauche bi
        :2e menu déroulant pour marges
        :checkbuttons pour CMI, GG, interpec
        et positionnant les radiobuttons utiles quand on sélection unilat :
        :radiobuttons sein droit uni, sein gauche uni, paroi droite uni et paroi gauche uni"""
        self.varSein_unilat.set(" ")
        self.varSeinG_bilat.set(" ")
        self.varSeinD_bilat.set(" ")

        self.radio_seinD_bilat.grid_forget()
        self.radio_paroiD_bilat.grid_forget()
        self.radio_seinG_bilat.grid_forget()
        self.radio_paroiG_bilat.grid_forget()
        self.label_Margin2.grid_forget()
        self.OptionMenuMargin2.grid_forget()

        self.gg_IMN2.grid_forget()
        self.gg_L12.grid_forget()
        self.gg_L22.grid_forget()
        self.gg_L32.grid_forget()
        self.gg_L42.grid_forget()
        self.gg_interpec2.grid_forget()

        self.radio_seinD_unilat.grid(row=4, column=0)
        self.radio_paroiD_unilat.grid(row=4, column=1)
        self.radio_seinG_unilat.grid(row=5, column=0)
        self.radio_paroiG_unilat.grid(row=5, column=1)

    def set_bilat(self):

        self.varSein_unilat.set(" ")
        self.varSeinG_bilat.set(" ")
        self.varSeinD_bilat.set(" ")

        self.radio_seinD_unilat.grid_forget()
        self.radio_paroiD_unilat.grid_forget()
        self.radio_seinG_unilat.grid_forget()
        self.radio_paroiG_unilat.grid_forget()

        self.radio_seinD_bilat.grid(row=4, column=0)
        self.radio_paroiD_bilat.grid(row=4, column=1)
        self.radio_seinG_bilat.grid(row=5, column=0)
        self.radio_paroiG_bilat.grid(row=5, column=1)

        self.gg_IMN2.grid(row=8, column=0)
        self.gg_L12.grid(row=8, column=1)
        self.gg_L22.grid(row=8, column=2)
        self.gg_L32.grid(row=8, column=3)
        self.gg_L42.grid(row=8, column=4)
        self.gg_interpec2.grid(row=8, column=5)

        self.label_Margin2.grid(row=4, column=2)
        self.OptionMenuMargin2.grid(row=4, column=3)

    def __init__(self):

        self.top = Tk()

        self.top.title("Traitement automatique en sénologie")

        self.top.resizable(0, 0)

        if DEBUG:
            tkinter.messagebox.showinfo("Information - DEBUG",
                                        "Mode débuggage, les RTStructs Annotate ne seront pas supprimés du répertoire d'importation de Raystation")

        # Initialisation des variables associées à chaque radiobutton

        # Variable partagée entre les techniques (3D, rIMRT/VMAT/TOMO)
        self.var3DVMAT = StringVar()
        self.var3DVMAT.set(" ")
        # Variable partagée entre les localisations (unilat/bilat)
        self.varBilat = StringVar()
        self.varBilat.set(" ")
        # Variable partagée entre le type (Sein D/Sein G/Paroi D/Paroi G) pour unilat
        self.varSein_unilat = StringVar()
        self.varSein_unilat.set(" ")
        # Variable partagée entre les types (Sein D/Paroi D) pour bilat
        self.varSeinG_bilat = StringVar()
        self.varSeinG_bilat.set(" ")
        # Variable partagée entre les types (Sein G/Paroi G) pour bilat
        self.varSeinD_bilat = StringVar()
        self.varSeinD_bilat.set(" ")

        # Création des radiobuttons pour technique, localisations et type

        # Lorsqu'on sélectionne le radiobutton pour la technique => ajustement des marges par défaut avec onClickRadio()
        self.radio_3D = Radiobutton(self.top, variable=self.var3DVMAT, text="3D/rIMRT", value="3D",
                                    command=self.onClickRadio)
        self.radio_VMAT = Radiobutton(self.top, variable=self.var3DVMAT, text="VMAT", value="VMAT",
                                      command=self.onClickRadio)
        self.radio_TOMO = Radiobutton(self.top, variable=self.var3DVMAT, text="TOMO", value="TOMO",
                                      command=self.onClickRadio)

        # Lorsqu'on sélectionne unilat/bilat -> ajustement des radiobuttons et checkbuttons concernés dans la fenêtre
        # avec set_unilat/set_bilat
        self.radio_unilat = Radiobutton(self.top, variable=self.varBilat, text="unilat", value="unilat",
                                        command=self.set_unilat)
        self.radio_bilat = Radiobutton(self.top, variable=self.varBilat, text="bilat", value="bilat",
                                       command=self.set_bilat)

        # Radiobuttons pour la latéralité et le type dans le cas unilat
        self.radio_seinD_unilat = Radiobutton(self.top, variable=self.varSein_unilat, text="sein droit uni",
                                              value="seinD_unilat")
        self.radio_paroiD_unilat = Radiobutton(self.top, variable=self.varSein_unilat, text="paroi droite uni",
                                               value="paroiD_unilat")
        self.radio_seinG_unilat = Radiobutton(self.top, variable=self.varSein_unilat, text="sein gauche uni",
                                              value="seinG_unilat")
        self.radio_paroiG_unilat = Radiobutton(self.top, variable=self.varSein_unilat, text="paroi gauche uni",
                                               value="paroiG_unilat")

        # Radiobuttons pour la latéralité et le type dans le cas bilat
        self.radio_seinD_bilat = Radiobutton(self.top, variable=self.varSeinD_bilat, text="sein droit bi",
                                             value="seinD_bilat")
        self.radio_paroiD_bilat = Radiobutton(self.top, variable=self.varSeinD_bilat, text="paroi droite bi",
                                              value="paroiD_bilat")

        self.radio_seinG_bilat = Radiobutton(self.top, variable=self.varSeinG_bilat, text="sein gauche bi",
                                             value="seinG_bilat")
        self.radio_paroiG_bilat = Radiobutton(self.top, variable=self.varSeinG_bilat, text="paroi gauche bi",
                                              value="paroiG_bilat")

        # Initialisation des variables associées à chaque checkbutton

        # Variables pour CMI, GG et interpec dans le cas unilat
        self.int_gg_IMN = IntVar()
        self.int_gg_L1 = IntVar()
        self.int_gg_L2 = IntVar()
        self.int_gg_L3 = IntVar()
        self.int_gg_L4 = IntVar()
        self.int_gg_interpec = IntVar()
        # Variables en doublon CMI, GG et interpec dans le cas bilat
        self.int_gg_IMN2 = IntVar()
        self.int_gg_L12 = IntVar()
        self.int_gg_L22 = IntVar()
        self.int_gg_L32 = IntVar()
        self.int_gg_L42 = IntVar()
        self.int_gg_interpec2 = IntVar()

        # Création des checkbuttons pour CMI, GG et interpec

        self.gg_IMN = Checkbutton(self.top, text="CMI", variable=self.int_gg_IMN)
        self.gg_L1 = Checkbutton(self.top, text="L1", variable=self.int_gg_L1)
        self.gg_L2 = Checkbutton(self.top, text="L2", variable=self.int_gg_L2)
        self.gg_L3 = Checkbutton(self.top, text="L3", variable=self.int_gg_L3)
        self.gg_L4 = Checkbutton(self.top, text="L4", variable=self.int_gg_L4)
        self.gg_interpec = Checkbutton(self.top, text="Interpec", variable=self.int_gg_interpec)

        # Création des checkbuttons pour CMI, GG et interpec en doublons dans le cas bilt

        self.gg_IMN2 = Checkbutton(self.top, text="CMI PTV G", variable=self.int_gg_IMN2)
        self.gg_L12 = Checkbutton(self.top, text="L1 PTV G", variable=self.int_gg_L12)
        self.gg_L22 = Checkbutton(self.top, text="L2 PTV G", variable=self.int_gg_L22)
        self.gg_L32 = Checkbutton(self.top, text="L3 PTV G", variable=self.int_gg_L32)
        self.gg_L42 = Checkbutton(self.top, text="L4 PTV G", variable=self.int_gg_L42)
        self.gg_interpec2 = Checkbutton(self.top, text="Interpec PTV G", variable=self.int_gg_interpec2)

        # Si bouton OK cliqué => vérifie que toutes les infos ont bien été renseignées et lance la fn create_struct()
        self.buttonOK = Button(self.top, text="OK", command=self.verif_radiobutton)
        self.buttonAnnuler = Button(self.top, text="Annuler", command=self.annulation)

        # Positionnement des radiobuttons et checkbuttons dans la pop up

        self.radio_3D.grid(row=2, column=0)
        self.radio_VMAT.grid(row=2, column=1)
        self.radio_TOMO.grid(row=2, column=2)
        self.radio_unilat.grid(row=3, column=0)
        self.radio_bilat.grid(row=3, column=1)

        self.radio_seinD_unilat.grid(row=4, column=0)
        self.radio_paroiD_unilat.grid(row=4, column=1)
        self.radio_seinG_unilat.grid(row=5, column=0)
        self.radio_paroiG_unilat.grid(row=5, column=1)

        self.gg_IMN.grid(row=7, column=0)
        self.gg_L1.grid(row=7, column=1)
        self.gg_L2.grid(row=7, column=2)
        self.gg_L3.grid(row=7, column=3)
        self.gg_L4.grid(row=7, column=4)
        self.gg_interpec.grid(row=7, column=5)

        Case = get_current("Case")
        # Récupération de la liste des noms des CTs du Case
        exam_list = find_exam(Case)
        patient = get_current("Patient")
        initial_rois_in_case = None
        patient.Save()

        phrase_case = "#############\nScript Seno Version : " + str(VersionScript) + "\nVersion Raystation : " + str(
            patient.ModificationInfo.SoftwareVersion) + "\nDate : " + str(Date_et_Heure) + "\nUtilisateur : " + str(
            patient.ModificationInfo.UserName)
        Case.Comments = phrase_case

        # S'il y a plus d'un CT : menu déroulant pour choisir sur lequel contourer
        self.label_exam = Label(self.top, text="CT à contourer : ", foreground='red', font='Calibri 12 bold')
        # self.label_exam.grid(row=1, column=1)
        self.listvariable_exam = ttk.Combobox(self.top, values=exam_list, width=40,
                                              state='readonly')
        self.listvariable_exam.grid(row=1, column=2, pady=10)


        # Création d'un menu déroulant pour la marge souhaitée
        self.label_Margin = Label(self.top, text="Retrait du PTV par rapport à la peau : ")
        self.listvariable_margin = StringVar()
        margin_list = ["0.1", "0.2", "0.3", "0.4", "0.5"]
        self.listvariable_margin.set(margin_list[2])  # Par défaut marge 0.3
        self.OptionMenuMargin = OptionMenu(self.top, self.listvariable_margin, *margin_list)

        # Création 2e menu déroulant pour la marge souhaitée dans le cas bilat
        self.label_Margin2 = Label(self.top, text="Retrait du PTV G par rapport à la peau : ")
        self.listvariable_margin2 = StringVar()
        margin_list2 = ["0.1", "0.2", "0.3", "0.4", "0.5"]
        self.listvariable_margin2.set(margin_list2[2])
        self.OptionMenuMargin2 = OptionMenu(self.top, self.listvariable_margin2, *margin_list2)

        # Positionnement menu déroulant list exam, margin et boutons OK et annuler
        # MANQUE POSITIONNEMENT MENU DEROULANT EXAMINATIONS
        self.label_exam.grid(row=1, column=1)
        self.label_Margin.grid(row=4, column=2)
        self.OptionMenuMargin.grid(row=4, column=3)

        self.buttonOK.grid(row=10, column=0, columnspan=2)
        self.buttonAnnuler.grid(row=10, column=1)

        self.top.mainloop()

main_window()

