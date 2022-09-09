from connect import *
# -*- coding: utf-8 -*-
from tkinter import*
import tkinter.ttk as ttk
import platform



try:
	Case=get_current('Case')
	Examination=get_current('Examination')
except:
	print('No case / examination selected')


Nom_CT_selectionne=Examination.Name

#Get ROI geometries for the syructure set of the current examination
roi_geometries=Case.PatientModel.StructureSets[Nom_CT_selectionne].RoiGeometries

##################################
#Obtenir la liste des OARs
###################################

OARs=[]

for roi in roi_geometries:
	if Case.PatientModel.RegionsOfInterest[roi.OfRoi.Name].Type =='Organ':
		OARs.append(roi.OfRoi.Name)

print(OARs)


##################################
#Obtenir la liste des PTV
###################################

PTVs=[]

for roi in roi_geometries:
	if Case.PatientModel.RegionsOfInterest[roi.OfRoi.Name].Type =='Ptv':
		PTVs.append(roi.OfRoi.Name)
        #print (roi.OfRoi.Name)



print("PTVs:",PTVs)


Nombre_de_PTV=len(PTVs)
print('Le nombre de PTV est :',Nombre_de_PTV)

##############
# Creation des z_OAR
#############


def stop():
	sys.exit()


gap=str(0)
PTV=str(0)

def show_entry_fields():
	global gap
	global PTV
	gap=e1.get()
	PTV=e2.get()
	print('gap et PTV',gap,PTV)

master2 = Tk()
master2.title('gap et PTV à utiliser pour la construction des z_OARs')
Label(master2, text="Gap entre l'OAR et le PTV (cm):").grid(row=1)
Label(master2, text="PTV à utiliser:").grid(row=2)


Valeurmarge1=StringVar()
Valeurmarge1.set("0.2")
#o = ttk.Combobox(root, values=["ligne 1", "ligne 2", "ligne 3", "ligne 4"])

#Valeurmarge2 = ttk.Combobox(master2, values=["ligne 1", "ligne 2", "ligne 3", "ligne 4"])
#o.pack ()

#Valeurmarge2=StringVar()
#Valeurmarge2.set("PTV Low Dose")

e1 = Entry(master2,textvariable=Valeurmarge1)
#e2 = Entry(master2,textvariable=Valeurmarge2)
e2=ttk.Combobox(master2, values=PTVs)
e1.grid(row=1, column=1)
e2.grid(row=2, column=1)
Button(master2, text='Arrêter le script', command=stop).grid(row=11, column=0, sticky=W, pady=4)
Button(master2, text='Continuer', command=lambda:[show_entry_fields(),master2.destroy()]).grid(row=11, column=2, sticky=W, pady=4)
mainloop( )



##########################



PTV_Inter=PTV
	
dict_z_OAR_a_creer ={}
for roi in OARs:
    Case.PatientModel.CreateRoi(Name=r"inters_OAR", Color="Black", Type="Organ", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
    Case.PatientModel.RegionsOfInterest['inters_OAR'].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [roi], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [PTV_Inter], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ResultOperation="Intersection", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
    Case.PatientModel.RegionsOfInterest['inters_OAR'].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
    if Case.PatientModel.StructureSets[Nom_CT_selectionne].RoiGeometries['inters_OAR'].HasContours() is True:
        dict_z_OAR_a_creer[roi]= 0
    else:
        dict_z_OAR_a_creer[roi]=1
    Case.PatientModel.RegionsOfInterest['inters_OAR'].DeleteRoi()







for roi in dict_z_OAR_a_creer:
    if dict_z_OAR_a_creer[roi]==0:
        print('z_roi a crer:',roi)
        color=Case.PatientModel.RegionsOfInterest[roi].Color
        nom=r"z_"+roi+'_'+PTV_Inter+'_gap_'+str(gap)
        Case.PatientModel.CreateRoi(Name=nom, Color=color, Type="undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.RegionsOfInterest[nom].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [roi], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [PTV_Inter], 'MarginSettings': { 'Type': "Expand", 'Superior': gap, 'Inferior': gap, 'Anterior': gap, 'Posterior': gap, 'Right': gap, 'Left': gap } }, ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
        Case.PatientModel.RegionsOfInterest[nom].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")

