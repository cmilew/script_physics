# Script recorded 22 Dec 2017

#   RayStation version: 6.1.1.2
#   Selected patient: ...

from connect import *
import sys
from tkinter import *

def checks_quit_script():
  """ Function aiming to close any pop-up when the red-cross is clicked """
  global quit_script
  if quit_script:
    print('Pop-up was quit by red-cross click -> exiting')
    sys.exit()
  quit_script = True


case = get_current("Case")
examination = get_current("Examination")


### TEST STUDY SHADOW ET STUDY INSTANCE UID #################################################################

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
print("Study instance UID :", study_instance_uid)
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
else:
    message = 'Le CT n\'est pas corrompu, vous pouvez contourer/faire la dosimétrie dessus.'

print(message)
if is_study_shadow or is_study_instance_uid_corrupted:
    quit_script = True
    root_pop_up = Tk()
    root_pop_up.title("")
    Label(root_pop_up, text=message, foreground='red', font='Calibri 12 bold').grid(row=1, column=1, padx=5, pady=5)
    Button(root_pop_up, text='OK', command=sys.exit, width=10).grid(row=2, column=1, padx=5, pady=5)
    root_pop_up.bind('<Return>', lambda event: sys.exit())
    root_pop_up.bind('<Escape>', lambda event: sys.exit())
    mainloop()
    checks_quit_script()

###################################################################################################################


with CompositeAction('ROI Algebra (External, Image set: CT 2)'):

  case.PatientModel.RegionsOfInterest['External'].CreateAlgebraGeometry(Examination=examination, Algorithm="Auto", ExpressionA={ 'Operation': "Union", 'SourceRoiNames': ["External"], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': ["Plot_grand_1", "Plot_grand_2", "Plot_grand_3", "Plot_grand_4", "Plot_petit_1", "Plot_petit_2"], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ResultOperation="Union", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })

  # CompositeAction ends 


with CompositeAction('Delete ROI (Plot_grand_1, Plot_grand_2, Plot_grand_3, Plot_grand_4, Plot_petit_1, Plot_petit_2)'):

  case.PatientModel.RegionsOfInterest['Plot_grand_1'].DeleteRoi()

  case.PatientModel.RegionsOfInterest['Plot_grand_2'].DeleteRoi()

  case.PatientModel.RegionsOfInterest['Plot_grand_3'].DeleteRoi()

  case.PatientModel.RegionsOfInterest['Plot_grand_4'].DeleteRoi()

  case.PatientModel.RegionsOfInterest['Plot_petit_1'].DeleteRoi()

  case.PatientModel.RegionsOfInterest['Plot_petit_2'].DeleteRoi()

  # CompositeAction ends 


