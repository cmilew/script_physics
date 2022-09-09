from connect import *
# -*- coding: utf-8 -*-
from tkinter import*
import tkinter.ttk as ttk
import platform
#from tkinter import messagebox as tkm
from tkinter.messagebox import*

try:
	Case=get_current('Case')
	Examination=get_current('Examination')
except:
	print('No case / examination selected')


Nom_CT_selectionne=Examination.Name


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


#Get ROI geometries for the syructure set of the current examination
roi_geometries=Case.PatientModel.StructureSets[Nom_CT_selectionne].RoiGeometries
##################################
#Obtenir la liste des PTV et ,nom du contour externe
###################################
PTVs=[]
for roi in roi_geometries:
	if Case.PatientModel.RegionsOfInterest[roi.OfRoi.Name].Type =='External':
		External=roi.OfRoi.Name
	if Case.PatientModel.RegionsOfInterest[roi.OfRoi.Name].Type =='Ptv':
		PTVs.append(roi.OfRoi.Name)
print("PTVs:",PTVs)
Nombre_de_PTV=len(PTVs)
print('Le nombre de PTV est :',Nombre_de_PTV)


            

#######################################################################################################
#######################################################################################################
#######################FONCTION RING##################################################################
#######################################################################################################
#######################################################################################################


def RING(PTV,Sup,Inf):

    nom='RING_'+PTV+'_'+Sup+'cm_'+Inf+'cm'
    color=Case.PatientModel.RegionsOfInterest[PTV].Color

    Case.PatientModel.CreateRoi(Name=nom, Color=color, Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
    Case.PatientModel.RegionsOfInterest[nom].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [PTV], 'MarginSettings': { 'Type': "Expand", 'Superior': Sup, 'Inferior': Sup, 'Anterior': Sup, 'Posterior': Sup, 'Right': Sup, 'Left': Sup } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [PTV], 'MarginSettings': { 'Type': "Expand", 'Superior': Inf, 'Inferior': Inf, 'Anterior': Inf, 'Posterior': Inf, 'Right': Inf, 'Left': Inf } }, ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
    Case.PatientModel.RegionsOfInterest[nom].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")

    return True
    
      

#######################################################################################################
#######################################################################################################
#######################CREATION RING #################################################################
#######################################################################################################
#######################################################################################################

def fenetre_creation_ring():
    PTV=str(0)
    Sup=str(0)
    Inf=str(0)
    result=str(0)

    def stop():
        sys.exit()
        
    def show_entry_fields():
        global PTV
        global Sup
        global Inf
        PTV=e1.get()
        Sup=e2.get()
        Inf=e3.get()
        print('PTV, Sup, Inf: ',PTV, Sup, Inf)
    

    master2 = Tk()
    master2.title('PTV et distances à utiliser pour la construction du Ring')
    Label(master2, text="PTV à utiliser:").grid(row=1)
    Label(master2, text="Distance Sup (cm)").grid(row=2)
    Label(master2, text="Distance Inf (cm)").grid(row=3)

    Valeurmarge2=StringVar()
    Valeurmarge2.set("1.5")
    Valeurmarge3=StringVar()
    Valeurmarge3.set("0.2")
    e1=ttk.Combobox(master2, values=PTVs)
    e2 = Entry(master2,textvariable=Valeurmarge2)
    e3 = Entry(master2,textvariable=Valeurmarge3)

    e1.grid(row=1, column=1)
    e2.grid(row=2, column=1)
    e3.grid(row=3, column=1)
    Button(master2, text='Arrêter le script', command=stop).grid(row=11, column=0, sticky=W, pady=4)
    Button(master2, text='Continuer', command=lambda:[show_entry_fields(),master2.destroy()]).grid(row=11, column=2, sticky=W, pady=4)
    mainloop( )

    
    return result
   
result=True
#while ring_creation==True:    
while (result==True):
    p=fenetre_creation_ring()
    r=RING(PTV,Sup,Inf)
    
