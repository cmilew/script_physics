# Script recorded 07 Dec 2017

#   RayStation version: 6.1.1.2
#   Selected patient: ...

from connect import *
from tkinter import *

patient=get_current("Patient")
case = get_current("Case")
examination = get_current("Examination")


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

################################################################################################################


ss=case.PatientModel.StructureSets[examination.Name]
# Get names of all ROIs defined for the current plan
roi_names = [r.OfRoi.Name for r in ss.RoiGeometries]


#Updater les structures sauf les CTV

for i, roi in enumerate(roi_names):
    if case.PatientModel.RegionsOfInterest[roi].Type is not "Ctv":
        r = case.PatientModel.RegionsOfInterest[roi].DerivedRoiExpression
        r_string=str(r)
        #Si le type est None, il s'agit d'une structure non-derivee
        if not r_string == 'None' :
            with CompositeAction('Update derived geometry (roi)'):
                case.PatientModel.RegionsOfInterest[roi].UpdateDerivedGeometry(Examination=examination, Algorithm="Auto")
            # CompositeAction ends








