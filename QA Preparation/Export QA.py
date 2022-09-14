# -*- coding: utf-8 -*-
from connect import *
from tkinter import *
#import pandas as pd

import os
#-----------------------------------------------------------------------------------------------------------------------------------
#														EXPORT QA VMAT
#-----------------------------------------------------------------------------------------------------------------------------------
#Création : 
#Date Inconnue - M. Edouard
#
#Modification :
#29/05/2020 - J. Vautier : *correction script pour ne plus mélanger les RTD et RTP des beamsets.
#						   *cela se produisait lorsque le QA du beam set 2 était créé avant le QA du beam set 1
#11/06/2020 - A. Alexis : *correction script pour ne plus mélanger les RTD et les RTP lorsque plusieurs plans présent pour le patient.
#						  *le script exportait toujours les qa des beam sets du 1er plan créé
#30/09/2020 - J. Vautier : modification du répertoire d'exportation pour les Versas
#08/12/2020 - A. Alexis : ajout de la date du TDM dans le nom du répertoire de stockage en plus du nom du Beam Set 
#						  Nom du répertoire : TDM_dd-mm-aa_nomdubeamset
#
#-----------------------------------------------------------------------------------------------------------------------------------

try:
	patient = get_current('Patient')
	case = get_current('Case')
	plan=get_current('Plan')
	examination = get_current('Examination')
	beamset=get_current('BeamSet')
except:
	print('No patient or case has been loaded. Script terminated')
	exit()
	


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
    study_shadow_test = examination.GetStoredDicomTagValueForVerification(Group=0x0008, Element=0x0050)
    print(study_shadow_test)
except:
    is_study_shadow = True

# Study instance UID verification
study_instance_uid = str(examination.GetStoredDicomTagValueForVerification(Group=0x0020, Element=0x000D))
# Gets groups separated by '.'
groups = study_instance_uid.split('.')
# if group starts with 0 and is not '.0.', study instance uid is corrupted
is_study_instance_uid_corrupted = any(group.startswith('0') and group != '0' for group in groups)

# Message to display in pop up
if is_study_shadow and is_study_instance_uid_corrupted:
    message = 'Attention le CT "' + examination.Name + '" est un study shadow ET son study Instance UID du CT est ' \
                                                  'corrompu, contactez le physicien de garde (4905).'
elif is_study_shadow and is_study_instance_uid_corrupted == False:
    message = 'Attention, le CT "' + examination.Name + '" est un study shadow, contacter le physicien de garde (4905)'
elif is_study_shadow == False and is_study_instance_uid_corrupted:
    message = 'Attention le Study Instance UID du CT "' + examination.Name + '" est corrompu, contactez le physicien ' \
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

##############################################################################################################




number_of_plans=case.TreatmentPlans.Count
print(number_of_plans)
number_of_beamset=plan.BeamSets.Count
print(number_of_beamset)
number_of_qaplans=plan.VerificationPlans.Count
print(number_of_qaplans)

###################################################################################
###########################Création REPERTOIRES ###################################
###################################################################################

ID=patient.PatientID
Name=patient.Name
caractere='^'
Name_famille=Name.split(caractere)
Name_dossier=Name_famille[0]+' '+ID
print('Nom du dossier:',Name_dossier)

Plan_Name=plan.Name
#print("***************************")
print("PLAN IS:",Plan_Name)

patient.Save()

print("nb of beamset:",number_of_beamset)
print("Number of QA plan :", plan.VerificationPlans.Count)

for i_QAplan in range(number_of_qaplans):

	#print("QA PLAN NAME REFERRED TO",plan.VerificationPlans[i_QAplan].ForTreatmentPlan.Name)
	if plan.VerificationPlans[i_QAplan].ForTreatmentPlan.Name == Plan_Name:
		print('_____________________________________')
		print('i_BS:',i_QAplan)   
		Name_BS=plan.VerificationPlans[i_QAplan].OfRadiationSet.DicomPlanLabel
		Name_Plan=plan.VerificationPlans[i_QAplan].ForTreatmentPlan.Name
		Name_Plan=Name_Plan.replace('/','-')
		Name_Plan=Name_Plan.replace('.','-')
		#print("Name_BS:",Name_BS)
		machine = beamset.MachineReference.MachineName
		
		if machine == "NOVALIS":
			repertoire=r'\\nas-01\PHY_PROC\Radiotherapie\CQ IMRT-IMAT-STEREO\NOVALIS\ARCCHECK\Patient Plans_VMAT'
		else:
			#repertoire=r'\\nas-01\PHY_PROC\Radiotherapie\CQ IMRT-IMAT-STEREO\VERSAHD\Patient Plans'
			repertoire=r'\\nas-01\Controle_Qualite_Patient\VERSAHD\Patient Plans'
		repertoire2=os.path.join(repertoire, Name_dossier)
		print(repertoire2)

		try: 
			os.makedirs(repertoire2)
			print("repertoire:",repertoire2)
		except:
			print("le dossier du patient existe déjà")
		
	
		path=os.path.join(repertoire2, 'TDM_'+Name_Plan+'_'+Name_BS)

		print("path final:",path)
		try: 
			os.makedirs(path)
		except:
			print("le dossier du patient existe déjà")
		
		
	##########################################################################################################################
	#########EXPORT DICOM
	#######################################################################################################################

		plan.VerificationPlans[i_QAplan].ScriptableQADicomExport ( ExportFolderPath=path, QaPlanIdentity = "Phantom" ,
		ExportExamination  = False,
		ExportExaminationStructureSet = True ,
		ExportBeamSet  = True ,
		ExportBeamSetDose  = True,
		ExportBeamSetBeamDose = False,
		IgnorePreConditionWarnings = True)

		# Supprimer le RStructure
		list_file = os.listdir(path)          # liste des fichiers dans le dossier
		for i_file in list_file:
			if i_file.startswith("RS"):
				path_file_RS = os.path.join(path, i_file)
				os.remove(path_file_RS) 
	
patient.Save()


	








