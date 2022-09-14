#######################################
# DESCRIPTION : création d'une ROI avec les décalages de l'option ROBUST et vérification de l'application de l'option
# ROBUST sur l'ensemble des contraintes et objectifs de l'optimiseur.
# On vérifie que le pamamètre 'Universal' de l'option ROBUST est bien cochée,
# sinon le script le sélectionne et invalide la dosimétrie.
#
# Auteur : Vautier
#
# Version 1.0 : Création du script
# Version 1.1 : Correction de bug (absence de ROI robust et absence de ROI 'External',
#               changement du nom de la ROI créée. La dosimétrie est invalidée si les pamamètres de
#               l'option ROBUST ne sont pas corrects.
# Version 1.2 : Correction de bug (volume Robust en type 'Control' au lieu de 'Undefined' pour que
#               Mosaiq charge le contours
# Version 2.0 : Modification du script : la dosimétrie reste valide si l'option ROBUST n'est pas appliquée
# Version 3.0 : CM - Modification du script pour prendre en compte tous les beamsets d'un plan.
#######################################

from connect import *
from tkinter import *
import tkinter.messagebox
import time

plan = get_current('Plan')
case = get_current('Case')
examination = get_current('Examination')

root = tkinter.Tk()
root.withdraw()


for plan_optimization in plan.PlanOptimizations:
    roi_names = [b.Name for b in case.PatientModel.RegionsOfInterest]

    dict_roi_robust = [cf.ForRegionOfInterest.Name for cf in plan_optimization.Objective.ConstituentFunctions
                       if cf.UseRobustness]
    dict_roi_robust += [cf.ForRegionOfInterest.Name for cf in plan_optimization.Constraints
                        if cf.UseRobustness and type(cf) != 'NoneType']

    if not roi_names:
        tkinter.messagebox.showerror('Erreur', f'Pas de ROI dans le case en cours')
    elif not dict_roi_robust:
        tkinter.messagebox.showerror('Erreur', f'Aucune ROI n\'a l\'option Robust')
    else:
        # on récupère les paramètres de décalage de ROBUST
        position_uncertainty_parameters = plan_optimization.OptimizationParameters.RobustnessParameters.\
            PositionUncertaintyParameters
        anterior = position_uncertainty_parameters.PositionUncertaintyAnterior
        inferior = position_uncertainty_parameters.PositionUncertaintyInferior
        left = position_uncertainty_parameters.PositionUncertaintyLeft
        posterior = position_uncertainty_parameters.PositionUncertaintyPosterior
        right = position_uncertainty_parameters.PositionUncertaintyRight
        superior = position_uncertainty_parameters.PositionUncertaintySuperior

        # on récupère et on modifie si besoin le paramètre 'PositionUncertaintySetting' qui doit être sur 'Universal'.
        # La dosimétrie est alors invalidée.
        position_uncertainty_setting = position_uncertainty_parameters.PositionUncertaintySetting
        if position_uncertainty_setting != 'Universal':
            tkinter.messagebox.showerror('Erreur', f'L\'option ROBUST va être reparamétrée avec le paramètre '
                                                   f'"Universal" au lieu de "{position_uncertainty_setting}"\n'
                                                   f'L\'optimisation va être réinitialisée !')
            # si le plan est déjà approuvé : erreur car on ne peut pas modifié les paramètres de l'option ROBUST
            if case.QueryPlanInfo(Filter={'Name': plan.Name})[0]['IsApproved']:
                tkinter.messagebox.showerror('Erreur',
                                             f'Le plan ne doit pas être approuvé pour le fonctionnement du script\n'
                                             f'Aucune modification n\'a été faite')
                exit(-1)
            position_uncertainty_setting = 'Universal'
            plan_optimization.ResetOptimization()
            exit(-1)

        # On demande à l'utilisateur si on crée la ROI avec les marges de l'option ROBUST
        for roi in dict_roi_robust:
            question_robust = f'Créer la ROI Robust pour {roi} ?\n' + \
                              (f'anterieur : {anterior}cm\n' if anterior else '') + \
                              (f'posterieur : {posterior}cm\n' if posterior else '') + \
                              (f'gauche : {left}cm\n' if left else '') + \
                              (f'droite : {right}cm\n' if right else '') + \
                              (f'inferieur : {inferior}cm\n' if inferior else '') + \
                              (f'superieur : {superior}cm\n' if superior else '')
            if tkinter.messagebox.askyesno('Question', question_robust):
                # Si une ROI du même nom que la ROI créée par le script existe, on demande si on veut l'écraser
                # ou nommer _1 (ou _2 ou _3 etc...) la ROI nouvellement créée.
                roi_name = 'Robust_'+roi
                if roi_name in roi_names:
                    question = f'{roi_name} déjà existante. Ecraser la roi {roi_name}?\n' \
                               f'Si non ou si la structure est déjà approuvée, une nouvelle ROI {roi_name} ' \
                               f'sera créée avec un numéro'
                    # Si des structures sont approuvées, on crée une nouvelle structure pour éviter tout plantage
                    if tkinter.messagebox.askyesno('Question', question):
                        if not case.PatientModel.StructureSets[examination.Name].ApprovedStructureSets:
                            case.PatientModel.RegionsOfInterest[roi_name].DeleteRoi()
                            roi_names.remove(roi_name)
                            time.sleep(1)

                    i = 0
                    new_roi_name = roi_name
                    while new_roi_name in roi_names:
                        i = i + 1
                        new_roi_name = roi_name + f'_{i}'
                    roi_name = new_roi_name
                case.PatientModel.CreateRoi(Name=roi_name, Color='white', Type='Control', TissueName=None,
                                            RbeCellTypeName=None, RoiMaterial=None)
                ExpressionA = {'Operation': 'Union', 'SourceRoiNames': [roi], 'MarginSettings': {
                    'Type': 'Expand', 'Superior': superior, 'Inferior': inferior, 'Anterior': anterior,
                    'Posterior': posterior, 'Right': right, 'Left': left}}
                ExpressionB = {'Operation': 'Union', 'SourceRoiNames': [], 'MarginSettings': {
                    'Type': 'Expand', 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0, 'Posterior': 0.0,
                    'Right': 0.0, 'Left': 0.0}}
                ResultMarginSettings = {'Type': 'Contract', 'Superior': 0.0, 'Inferior': 0.0, 'Anterior': 0.0,
                                        'Posterior': 0.0, 'Right': 0.0, 'Left': 0.0}
                case.PatientModel.RegionsOfInterest[roi_name].CreateAlgebraGeometry(
                    Examination=examination, Algorithm='Auto', ExpressionA=ExpressionA, ExpressionB=ExpressionB,
                    ResultOperation='None', ResultMarginSettings=ResultMarginSettings)

