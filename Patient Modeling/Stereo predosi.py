from connect import *
# -*- coding: utf-8 -*-
from tkinter import *
import tkinter.ttk as ttk
import platform


########################################
########################################
###########  FONCTIONS #################
########################################
########################################
def create_roi(nom_roi, Color, type):
    try:
        Case.PatientModel.CreateRoi(Name=nom_roi, Color=Color, Type=type, TissueName=None, RbeCellTypeName=None,
                                    RoiMaterial=None)
    except:
        print(nom_roi, " existe deja")
    return True


def soustraire_2_contours_List(Name_1, Name_List_2, marge_1, marge_2, type_marge1, type_marge2, Name_Somme, Color,
                               Type):
    try:
        Case.PatientModel.CreateRoi(Name=Name_Somme, Color=Color, Type=Type, TissueName=None, RbeCellTypeName=None,
                                    RoiMaterial=None)
        Case.PatientModel.RegionsOfInterest[Name_Somme].SetAlgebraExpression(
            ExpressionA={'Operation': "Union", 'SourceRoiNames': [Name_1],
                         'MarginSettings': {'Type': type_marge1, 'Superior': marge_1, 'Inferior': marge_1,
                                            'Anterior': marge_1, 'Posterior': marge_1, 'Right': marge_1,
                                            'Left': marge_1}},
            ExpressionB={'Operation': "Union", 'SourceRoiNames': Name_List_2,
                         'MarginSettings': {'Type': type_marge2, 'Superior': marge_2, 'Inferior': marge_2,
                                            'Anterior': marge_2, 'Posterior': marge_2, 'Right': marge_2,
                                            'Left': marge_2}}, ResultOperation="Subtraction",
            ResultMarginSettings={'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0,
                                  'Right': 0, 'Left': 0})
        Case.PatientModel.RegionsOfInterest[Name_Somme].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
        result = True
    except:
        print("ATTENTION, ", Name_1, " ou ", Name_List_2, " n'existent pas OU ", Name_Somme, " existe déjà!")
        result = False
    return result


def soustraire_2_contours(Name_1, Name_2, marge_1, marge_2, type_marge1, type_marge2, Name_Somme, Color, Type_ROI):
    try:
        Case.PatientModel.CreateRoi(Name=Name_Somme, Color=Color, Type=Type_ROI, TissueName=None, RbeCellTypeName=None,
                                    RoiMaterial=None)
        Case.PatientModel.RegionsOfInterest[Name_Somme].SetAlgebraExpression(
            ExpressionA={'Operation': "Union", 'SourceRoiNames': [Name_1],
                         'MarginSettings': {'Type': type_marge1, 'Superior': marge_1, 'Inferior': marge_1,
                                            'Anterior': marge_1, 'Posterior': marge_1, 'Right': marge_1,
                                            'Left': marge_1}},
            ExpressionB={'Operation': "Union", 'SourceRoiNames': [Name_2],
                         'MarginSettings': {'Type': type_marge2, 'Superior': marge_2, 'Inferior': marge_2,
                                            'Anterior': marge_2, 'Posterior': marge_2, 'Right': marge_2,
                                            'Left': marge_2}}, ResultOperation="Subtraction",
            ResultMarginSettings={'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0,
                                  'Right': 0, 'Left': 0})
        Case.PatientModel.RegionsOfInterest[Name_Somme].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
        result = True
    except:
        print("ATTENTION, ", Name_1, " ou ", Name_2, " n'existent pas OU ", Name_Somme, " existe déjà!")
        result = False
    return result


def creation_structures_stereo(PTV, gap, rep, PRVs, GTV, Nom_CT_selectionne):
    structures = ["PTV-PRV", "z_SHELL1_2mm", "z_SHELL2_15mm", "z_SHELL3_30mm", "z_SHELL4_45mm", "z_PTV_OPT",
                  "z_GTV_OPT", "z_GTV_125%", "ZZ_Dmax_2cm"]
    if rep == "NON":
        structures = ["PTV-PRV", "z_SHELL1_2mm", "z_SHELL2_15mm", "z_SHELL3_30mm", "z_SHELL4_45mm", "z_PTV_OPT",
                      "z_GTV_OPT", "z_GTV_125%", "ZZ_Dmax_2cm"]
    else:
        structures = [PTV + "-PRV", "z_SHELL1_2mm_" + PTV, "z_SHELL2_15mm_" + PTV, "z_SHELL3_30mm_" + PTV,
                      "z_SHELL4_45mm_" + PTV, "z_PTV_OPT_" + PTV, "z_GTV_OPT_" + PTV, "z_GTV_125%_" + PTV,
                      "ZZ_Dmax_2cm_" + PTV]

    if len(PRVs) > 0:
        PTV_PRV = soustraire_2_contours_List(PTV, PRVs, 0, gap, "Expand", "Expand", structures[0], "Aqua", "Ptv")
	# S'il n'y a pas de PRV le PTV-PRV = PTV
    else:
        PTV_PRV = Case.PatientModel.CreateRoi(Name=structures[0], Color="Aqua", Type="Ptv", TissueName=None,
									RbeCellTypeName=None, RoiMaterial=None)
        PTV_PRV.SetAlgebraExpression(ExpressionA={'Operation': "Union", 'SourceRoiNames': [PTV],
													   'MarginSettings': {'Type': "Expand", 'Superior': 0,
																		  'Inferior': 0, 'Anterior': 0, 'Posterior': 0,
																		  'Right': 0, 'Left': 0}},
										  ExpressionB={'Operation': "Union", 'SourceRoiNames': [],
													   'MarginSettings': {'Type': "Expand", 'Superior': 0,
																		  'Inferior': 0, 'Anterior': 0, 'Posterior': 0,
																		  'Right': 0, 'Left': 0}},
										  ResultOperation="None",
										  ResultMarginSettings={'Type': "Expand", 'Superior': 0, 'Inferior': 0,
																'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0})

        PTV_PRV.UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
    z_Shell1_2mm = soustraire_2_contours(structures[0], structures[0], 0.4, 0.2, "Expand", "Expand", structures[1],
                                         "128, 128, 255", "Undefined")
    z_Shell1_15mm = soustraire_2_contours(structures[0], structures[0], 1.7, 1.5, "Expand", "Expand", structures[2],
                                          "Purple", "Undefined")
    z_Shell1_30mm = soustraire_2_contours(structures[0], structures[0], 3.2, 3.0, "Expand", "Expand", structures[3],
                                          "Brown", "Undefined")
    z_Shell1_45mm = soustraire_2_contours(structures[0], structures[0], 4.7, 4.5, "Expand", "Expand", structures[4],
                                          "Yellow", "Undefined")
    zz_dmax_2cm = soustraire_2_contours(structures[0], structures[0], 2.05, 1.95, "Expand", "Expand", structures[8],
                                        "Blue", "Undefined")
    z_PTV_Opt = soustraire_2_contours(structures[0], GTV, 0, 0, "Expand", "Expand", structures[5], "Blue", "Undefined")

    r = create_roi(structures[6], "Green", "Undefined")
    Case.PatientModel.RegionsOfInterest[structures[6]].SetAlgebraExpression(
        ExpressionA={'Operation': "Union", 'SourceRoiNames': [GTV],
                     'MarginSettings': {'Type': "Contract", 'Superior': 0.2, 'Inferior': 0.2, 'Anterior': 0.2,
                                        'Posterior': 0.2, 'Right': 0.2, 'Left': 0.2}},
        ExpressionB={'Operation': "Union", 'SourceRoiNames': [],
                     'MarginSettings': {'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0,
                                        'Right': 0, 'Left': 0}}, ResultOperation="None",
        ResultMarginSettings={'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0,
                              'Left': 0})
    Case.PatientModel.RegionsOfInterest[structures[6]].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")

    # z_GTV_125=soustraire_2_contours(GTV,"",0,0,"Expand","Expand",structures[7],"Orange","Undefined")
    Coord = Case.PatientModel.StructureSets[Nom_CT_selectionne].RoiGeometries[GTV].GetCenterOfRoi()
    print("Coord:", Coord)

    Case.PatientModel.CreateRoi(Name=structures[7], Color="Orange", Type="Undefined", TissueName=None,
                                RbeCellTypeName=None, RoiMaterial=None)
    Case.PatientModel.RegionsOfInterest[structures[7]].CreateSphereGeometry(Radius=0.3, Examination=Examination,
                                                                            Center={'x': Coord.x, 'y': Coord.y,
                                                                                    'z': Coord.z},
                                                                            Representation="Voxels", VoxelSize=None)

    r = create_roi("SCRIPT " + PTV + " " + GTV + " " + gap + " " + rep, "Black", "Undefined")
    return True


########################################
########################################
###########  MAIN ######################
########################################
########################################


###VARIABLES
try:
    Case = get_current('Case')
    Examination = get_current('Examination')
except:
    print('No case / examination selected')

Nom_CT_selectionne = Examination.Name
roi_geometries = Case.PatientModel.StructureSets[Nom_CT_selectionne].RoiGeometries


# STUDY SHADOW & STUDY INSTANCE UID TEST ########################################

def checks_quit_script():
    """ Function aiming to close any pop-up when the red-cross is clicked """
    global quit_script
    if quit_script:
        print('Pop-up was quit by red-cross click -> exiting')
        sys.exit()
    quit_script = True


is_study_shadow = False
is_study_instance_uid_corrupted = False

# Study shadow test
try:
    study_shadow_test = Examination.GetStoredDicomTagValueForVerification(Group=0x0008, Element=0x0050)
    print(study_shadow_test)
except:
    is_study_shadow = True

# Study instance UID verification
study_instance_uid = str(Examination.GetStoredDicomTagValueForVerification(Group=0x0020, Element=0x000D))
# Gets groups separated by '.'
groups = study_instance_uid.split('.')
# if group starts with 0 and is not '.0.', study instance uid is corrupted
is_study_instance_uid_corrupted = any(group.startswith('0') and group != '0' for group in groups)

# Message to display in pop up
if is_study_shadow and is_study_instance_uid_corrupted:
    message = 'Attention le CT "' + Nom_CT_selectionne + '" est un study shadow ET son study Instance UID du CT est ' \
                                                         'corrompu, contactez le physicien de garde (4905).'
elif is_study_shadow and is_study_instance_uid_corrupted == False:
    message = 'Attention, le CT "' + Nom_CT_selectionne + '" est un study shadow, contacter le physicien de garde (4905)'
elif is_study_shadow == False and is_study_instance_uid_corrupted:
    message = 'Attention le Study Instance UID du CT "' + Nom_CT_selectionne + '" est corrompu, contactez le physicien ' \
                                                                               'de garde (4905).'
quit_script = True
if is_study_shadow or is_study_instance_uid_corrupted:
    print(message)
    root_pop_up = Tk()
    root_pop_up.title("")
    Label(root_pop_up, text=message, foreground='red', font='Calibri 12 bold').grid(row=1, column=1, padx=5, pady=5)
    Button(root_pop_up, text='OK', command=sys.exit, width=10).grid(row=2, column=1, padx=5, pady=5)
    root_pop_up.bind('<Return>', lambda event: sys.exit())
    root_pop_up.bind('<Escape>', lambda event: sys.exit())
    mainloop()
    checks_quit_script()

################################################################################################################

GTVs = []
for roi in roi_geometries:
    if Case.PatientModel.RegionsOfInterest[roi.OfRoi.Name].Type == 'Gtv':
        GTVs.append(roi.OfRoi.Name)
Nombre_GTV = len(GTVs)

CTVs = []
for roi in roi_geometries:
    if Case.PatientModel.RegionsOfInterest[roi.OfRoi.Name].Type == 'Ctv':
        CTVs.append(roi.OfRoi.Name)
Nombre_CTV = len(CTVs)

PTVs = []
for roi in roi_geometries:
    if Case.PatientModel.RegionsOfInterest[roi.OfRoi.Name].Type == 'Ptv':
        PTVs.append(roi.OfRoi.Name)
Nombre_PTV = len(PTVs)

PRVs_TOT = ["PRV Moelle 2mm", "PRV Queue de cheval 2mm", "PRV Oesophage 2 mm"]
print(
    "Attention, la liste des PRV testés est : PRV Moelle 2mm , PRV Queue de cheval , PRV Oesophage 2 mm pour la construction du PTV-PRV")
PRVs = []
for roi in PRVs_TOT:
    temp = False
    try:
        # Case.PatientModel.RegionsOfInterest[roi].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
        r = Case.PatientModel.StructureSets[Nom_CT_selectionne].RoiGeometries[roi].HasContours()
        if r == True:
            temp = True
    except:
        print("Le PRV ", roi, "n'a pas de contours ou a été supprimé")
    if temp == True:
        PRVs.append(roi)
print("PRVs:", PRVs)

Reponse = ["NON", "OUI"]


def stop():
    sys.exit()


gap = str(0)
PTV = str(0)
rep = str(0)
GTV = str(0)


def show_entry_fields():
    global gap
    global PTV
    global rep
    global GTV
    global quit_script
    gap = e1.get()
    PTV = e2.get()
    GTV = e3.get()
    rep = e4.get()
    quit_script = False

master2 = Tk()
master2.title("gap et PTV à utiliser pour la construction des structures d'optimisation")
Label(master2, text="Gap entre les PRV et le PTV (cm):").grid(row=1)
Label(master2, text="PTV à utiliser:").grid(row=2)
Label(master2, text="GTV à utiliser").grid(row=3)
Label(master2, text="Plusieurs PTV ?").grid(row=4)

Valeurmarge1 = StringVar()
Valeurmarge1.set("0.2")

e1 = Entry(master2, textvariable=Valeurmarge1)
e2 = ttk.Combobox(master2, values=PTVs)
e3 = ttk.Combobox(master2, values=GTVs)
e4 = ttk.Combobox(master2, values=Reponse)
e1.grid(row=1, column=1)
e2.grid(row=2, column=1)
e3.grid(row=3, column=1)
e4.grid(row=4, column=1)
Button(master2, text='Arrêter le script', command=stop).grid(row=11, column=0, sticky=W, pady=4)
Button(master2, text='Continuer', command=lambda: [show_entry_fields(), master2.destroy()]).grid(row=11, column=2,
                                                                                                 sticky=W, pady=4)
mainloop()
checks_quit_script()
# SI un seul PTV --> on ne change pas les noms pour que les template d'obj fonctionnent --> PTV-PRV ....
# Si plusieurs PTV, on utilise le nom du PTV

r = creation_structures_stereo(PTV, gap, rep, PRVs, GTV, Nom_CT_selectionne)