from connect import *
from tkinter import *

try:
	patient=get_current('Patient')
	case=get_current('Case')
	plan=get_current('Plan')
	beam_set=get_current('BeamSet')
	examination=get_current('Examination')
except:
	print('there is no plan/Beamset')
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



#########################################
#condition, sur le type de prescription ! 3D: prescription en 1 point
#########################################
if beam_set.Prescription.PrimaryPrescriptionDoseReference.PrescriptionType == 'DoseAtPoint':
	#Nom point de pres:
	Nom=beam_set.Prescription.PrimaryPrescriptionDoseReference.OnStructure.Name
	print(Nom)

	#coord point de pres:
	Coord=case.PatientModel.StructureSets[examination.Name].PoiGeometries[Nom].Point
	print(Coord)
	Name_DSP='DSP_'+Nom
	print(Name_DSP)
	beam_set.CreateDoseSpecificationPoint(Name=Name_DSP, Coordinates={'x': Coord.x, 'y': Coord.y, 'z': Coord.z }, VisualizationDiameter=1)
	
	
	for beam in beam_set.Beams:
		print(beam_set.Beams[beam.Name].Name)
		print(beam.Name)
		beam_set.Beams[beam.Name].SetDoseSpecificationPoint(Name=Name_DSP)
		#patient.Cases['CASE 1'].TreatmentPlans['test RS8B SP1 opti'].BeamSets['BOOST E-'].Beams['20BOOST E-'].Description
		#print(beam)
		



#####################################
#SI VMAT (prescription en dose Médiane
########################		
if beam_set.Prescription.PrimaryPrescriptionDoseReference.PrescriptionType == 'MedianDose':
	Dose_prescrite=beam_set.Prescription.PrimaryPrescriptionDoseReference.DoseValue

	
	# create ROI from DoseAtPoint
	indice=beam_set.Number-1
	print(indice)
	plan_dose=plan.TreatmentCourse.TotalDose.WeightedDoseReferences[indice].DoseDistribution
	weight=plan.TreatmentCourse.TotalDose.WeightedDoseReferences[indice].Weight
	threshold_level=Dose_prescrite/weight
	
	
	print(threshold_level)
	roi_name='Control_'+str(Dose_prescrite)
	roi=case.PatientModel.CreateRoi(Name=roi_name,Color='Blue',Type='Control')
	roi.CreateRoiGeometryFromDose(DoseDistribution=plan_dose,ThresholdLevel=threshold_level)
	
	Coord=case.PatientModel.StructureSets[examination.Name].RoiGeometries[roi_name].PrimaryShape.Contours[0][0]
	
	
	Nom=beam_set.Prescription.PrimaryPrescriptionDoseReference.OnStructure.Name
	Name_DSP='Point_'+Nom
	beam_set.CreateDoseSpecificationPoint(Name=Name_DSP, Coordinates={'x': Coord.x, 'y': Coord.y, 'z': Coord.z }, VisualizationDiameter=1)
	for beam in beam_set.Beams:
		print(beam_set.Beams[beam.Name].Name)
		print(beam.Name)
		beam_set.Beams[beam.Name].SetDoseSpecificationPoint(Name=Name_DSP)
	
	
	
	
	
	
	
	
