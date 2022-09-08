from connect import *
# -*- coding: utf-8 -*-
from tkinter import*
import tkinter.ttk as ttk
import platform

from tkinter.messagebox import*

#Ajout 26/11/2020########################
#patient_db = get_current("PatientDB")
#templateNames = patient_db.GetTemplateMaterialNames()
#templateList = patient_db.GetTemplateMaterial()
#template = [x for x in templateList.Materials if x.Name == "Water"]
##########################

try:
    Case=get_current('Case')
    Examination=get_current('Examination')
except:
    print('No case / examination selected')


Nom_CT_selectionne=Examination.Name
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

##################################
#Obtenir la liste des OARs
###################################

OARs=[]

for roi in roi_geometries:
    if Case.PatientModel.RegionsOfInterest[roi.OfRoi.Name].Type =='Organ':
        OARs.append(roi.OfRoi.Name)

print(OARs)

#########################################################################################
#########################################################################################
#########################################################################################


############
#ARTEFACTS
############
try:
    Case.PatientModel.CreateRoi(Name=r"Artefact", Color="Brown", Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
    if Case.PatientModel.Materials[0].Name == 'Water':
       Case.PatientModel.RegionsOfInterest['Artefact'].SetRoiMaterial(Material=Case.PatientModel.Materials[0])
    else: 
       print("Attention, La densite des artefacts n'a pas pu etre affectee")
    #Case.PatientModel.RegionsOfInterest['Artefact'].SetRoiMaterial(Material=template[0])
except:
    print("Artefact existe déjà")

##############
# DUMMYs
#############
try:
    color=System.Drawing.Color.FromArgb(255,128,0,64)
    Case.PatientModel.CreateRoi(Name=r"Dummy cerveau", Color=color, Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
    Case.PatientModel.CreateRoi(Name=r"Dummy cou", Color='Purple', Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
    color=System.Drawing.Color.FromArgb(255,64,0,64)
    Case.PatientModel.CreateRoi(Name=r"Dummy BM", Color=color, Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
    color=System.Drawing.Color.FromArgb(255,192,0,192)
    Case.PatientModel.CreateRoi(Name=r"Dummy lat", Color=color, Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
except:
    print("les dummy existent déjà")

###################
# PRV Moelle (3mm)
###################
try:
    if Case.PatientModel.StructureSets[Nom_CT_selectionne].RoiGeometries['Moelle'].HasContours()==True:
        Case.PatientModel.CreateRoi(Name=r"PRV Moelle", Color='Yellow', Type="Organ", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.RegionsOfInterest["PRV Moelle"].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [r"Moelle"], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0.3, 'Posterior': 0.3, 'Right': 0.3, 'Left': 0.3 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ResultOperation="None", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
        Case.PatientModel.RegionsOfInterest["PRV Moelle"].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
except:
    print("PRV moelle existe deja")
###################
# PRV Tronc (3mm)
###################
try:
    if Case.PatientModel.StructureSets[Nom_CT_selectionne].RoiGeometries['Tronc Cérébral'].HasContours()==True:
        Case.PatientModel.CreateRoi(Name=r"PRV Tronc Cérébral", Color='Orange', Type="Organ", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.RegionsOfInterest["PRV Tronc Cérébral"].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [r"Tronc Cérébral"], 'MarginSettings': { 'Type': "Expand", 'Superior': 0.3, 'Inferior': 0, 'Anterior': 0.3, 'Posterior': 0.3, 'Right': 0.3, 'Left': 0.3 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ResultOperation="None", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
        Case.PatientModel.RegionsOfInterest["PRV Tronc Cérébral"].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
except:
    print("PRV TC deja")
#########################
# PRV voies optique +2mm
#########################
try:
    OAR_optique=["Nerf Optique D","Nerf Optique G","Chiasma","Cochlée D","Cochlée G"]
    marge=0.2
    for roi in OAR_optique :
        if Case.PatientModel.StructureSets[Nom_CT_selectionne].RoiGeometries[roi].HasContours()==True:
            nom="PRV "+roi
            color=Case.PatientModel.RegionsOfInterest[roi].Color
            Case.PatientModel.CreateRoi(Name=nom, Color=color, Type="Organ", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
            Case.PatientModel.RegionsOfInterest[nom].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [roi], 'MarginSettings': { 'Type': "Expand", 'Superior': marge, 'Inferior': marge, 'Anterior': marge, 'Posterior': marge, 'Right': marge, 'Left': marge } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ResultOperation="None", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
            Case.PatientModel.RegionsOfInterest[nom].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
except:
    print("PRV optiques existent deja")

#########################################################################################
#########################################################################################
#########################################################################################

def RING(PTV,Sup,Inf):

    color=Case.PatientModel.RegionsOfInterest[PTV].Color
    Case.PatientModel.CreateRoi(Name=r"RING_TEMP", Color="Black", Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
    Case.PatientModel.RegionsOfInterest["RING_TEMP"].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [PTV], 'MarginSettings': { 'Type': "Expand", 'Superior': Sup, 'Inferior': Sup, 'Anterior': Sup, 'Posterior': Sup, 'Right': Sup, 'Left': Sup } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [PTV], 'MarginSettings': { 'Type': "Expand", 'Superior': Inf, 'Inferior': Inf, 'Anterior': Inf, 'Posterior': Inf, 'Right': Inf, 'Left': Inf } }, ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
    Case.PatientModel.RegionsOfInterest["RING_TEMP"].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
    #nom="NOM"
    nom='RING_'+PTV+'_'+str(Sup)+'_'+str(Inf)
    print("NOM:"+nom)
    
    Case.PatientModel.CreateRoi(Name=nom, Color=color, Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
    Case.PatientModel.RegionsOfInterest[nom].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [r"RING_TEMP"], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [External], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ResultOperation="Intersection", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
    Case.PatientModel.RegionsOfInterest[nom].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")

    Case.PatientModel.RegionsOfInterest["RING_TEMP"].DeleteRoi()
    return nom

def ring_ORL_3PTV(ring_name,r_ring,zz_a,zz_b):
    Case.PatientModel.RegionsOfInterest[ring_name].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [r_ring], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [zz_a, zz_b], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
    Case.PatientModel.RegionsOfInterest[ring_name].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
  #Case.PatientModel.StructureSets[Examination].SimplifyContours(RoiNames=[ring_name], RemoveHoles3D=False, RemoveSmallContours=True, AreaThreshold=0.1, ReduceMaxNumberOfPointsInContours=False, MaxNumberOfPoints=None, CreateCopyOfRoi=False, ResolveOverlappingContours=False)

    return True

def ring_ORL_2PTV(ring_name,r_ring,zz_a):
    #Case.PatientModel.CreateRoi(Name=ring_name, Color="Red", Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
    Case.PatientModel.RegionsOfInterest[ring_name].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [r_ring], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [zz_a], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
    Case.PatientModel.RegionsOfInterest[ring_name].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
    #Case.PatientModel.StructureSets[Examination].SimplifyContours(RoiNames=[ring_name], RemoveHoles3D=False, RemoveSmallContours=True, AreaThreshold=0.1, ReduceMaxNumberOfPointsInContours=False, MaxNumberOfPoints=None, CreateCopyOfRoi=False, ResolveOverlappingContours=False)

    return True

if Nombre_de_PTV ==1:
	if PTVs[0]=="PTV":
		Case.PatientModel.RegionsOfInterest[r"PTV"].Name = r"PTV High Dose"

################################################################################################
################################################################################################
#############  3 PTV ############################################################################
################################################################################################
################################################################################################

if Nombre_de_PTV ==3:
    #########################
    # PTV dosi
    #########################
    Gap_LD=0.2
    Gap_MD=0.2
    try:
        nom="z_PTV Low Dose"
        color=Case.PatientModel.RegionsOfInterest[r"PTV Low Dose"].Color
        Case.PatientModel.CreateRoi(Name=nom, Color=color, Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.RegionsOfInterest[nom].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [r"PTV Low Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [r"PTV Medium Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': Gap_LD, 'Inferior': Gap_LD, 'Anterior': Gap_LD, 'Posterior': Gap_LD, 'Right': Gap_LD, 'Left': Gap_LD } }, ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
        Case.PatientModel.RegionsOfInterest[nom].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
        nom="z_PTV Medium Dose"
        color=Case.PatientModel.RegionsOfInterest["PTV Medium Dose"].Color
        Case.PatientModel.CreateRoi(Name=nom, Color=color, Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.RegionsOfInterest[nom].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [r"PTV Medium Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [r"PTV High Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': Gap_MD, 'Inferior': Gap_MD, 'Anterior': Gap_MD, 'Posterior': Gap_MD, 'Right': Gap_MD, 'Left': Gap_MD } }, ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
        Case.PatientModel.RegionsOfInterest[nom].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
    except:
        print("z_PTV dosi existent deja")





    #Gap PTV LOw dose: 1.5cm; Md=1cm
    Gap_LD=1.5
    Gap_MD=1
    
    try:
        nom="z_PTV Low Dose "+str(Gap_LD)+"cm"
        color=Case.PatientModel.RegionsOfInterest[r"PTV Low Dose"].Color
        Case.PatientModel.CreateRoi(Name=nom, Color=color, Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.RegionsOfInterest[nom].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [r"PTV Low Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [r"PTV Medium Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': Gap_LD, 'Inferior': Gap_LD, 'Anterior': Gap_LD, 'Posterior': Gap_LD, 'Right': Gap_LD, 'Left': Gap_LD } }, ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
        Case.PatientModel.RegionsOfInterest[nom].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
        nom="z_PTV Medium Dose "+str(Gap_MD)+"cm"
        color=Case.PatientModel.RegionsOfInterest["PTV Medium Dose"].Color
        Case.PatientModel.CreateRoi(Name=nom, Color=color, Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.RegionsOfInterest[nom].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [r"PTV Medium Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [r"PTV High Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': Gap_MD, 'Inferior': Gap_MD, 'Anterior': Gap_MD, 'Posterior': Gap_MD, 'Right': Gap_MD, 'Left': Gap_MD } }, ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
        Case.PatientModel.RegionsOfInterest[nom].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
    except:
        print("PTV dosi existent deja")
		
    Gap_LD=0
    Gap_MD=0
    
    try:
        nom="zz_PTV Low Dose"
        color=Case.PatientModel.RegionsOfInterest[r"PTV Low Dose"].Color
        Case.PatientModel.CreateRoi(Name=nom, Color=color, Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.RegionsOfInterest[nom].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [r"PTV Low Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [r"PTV Medium Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': Gap_LD, 'Inferior': Gap_LD, 'Anterior': Gap_LD, 'Posterior': Gap_LD, 'Right': Gap_LD, 'Left': Gap_LD } }, ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
        Case.PatientModel.RegionsOfInterest[nom].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
        nom="zz_PTV Medium Dose"
        color=Case.PatientModel.RegionsOfInterest["PTV Medium Dose"].Color
        Case.PatientModel.CreateRoi(Name=nom, Color=color, Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.RegionsOfInterest[nom].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [r"PTV Medium Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [r"PTV High Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': Gap_MD, 'Inferior': Gap_MD, 'Anterior': Gap_MD, 'Posterior': Gap_MD, 'Right': Gap_MD, 'Left': Gap_MD } }, ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
        Case.PatientModel.RegionsOfInterest[nom].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
    except:
        print("zz_PTV dosi existent deja")        
    #########################
    # Ring
    #########################
    
    #TEMP_RING:
    
    try:
        Case.PatientModel.CreateRoi(Name=r"Ring_High_Dose", Color="Red", Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.CreateRoi(Name=r"Ring_Medium_Dose", Color="Green", Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.CreateRoi(Name=r"Ring_Low_Dose", Color="Blue", Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        r_PTV_HD=RING('PTV High Dose',1.5,0.3)
        r_PTV_MD=RING('PTV Medium Dose',1.5,0.3)
        r_PTV_LD=RING('PTV Low Dose',1.5,0.3)
    except:
        print("TEMP RING existent deja")
    

    try:
        Case.PatientModel.CreateRoi(Name=r"zz_PTV Low Dose", Color="Blue", Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.RegionsOfInterest[r"zz_PTV Low Dose"].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [r"PTV Low Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [r"PTV High Dose", r"PTV Medium Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
        Case.PatientModel.RegionsOfInterest[r"zz_PTV Low Dose"].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
        Case.PatientModel.CreateRoi(Name=r"zz_PTV Medium Dose", Color="Green", Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.RegionsOfInterest[r"zz_PTV Medium Dose"].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [r"PTV Medium Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [r"PTV Low Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
        Case.PatientModel.RegionsOfInterest[r"zz_PTV Medium Dose"].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
    except:
        print("zz_PTV existent deja")


    try:
        r=ring_ORL_3PTV(r"Ring_High_Dose",r_PTV_HD,r"zz_PTV Low Dose",r"zz_PTV Medium Dose")
        r=ring_ORL_3PTV(r"Ring_Medium_Dose",r_PTV_MD,r"zz_PTV Low Dose",r"Ring_High_Dose")
        r=ring_ORL_3PTV(r"Ring_Low_Dose",r_PTV_LD,r"Ring_Medium_Dose",r"Ring_High_Dose")
		
#        Case.PatientModel.StructureSets[Examination].SimplifyContours(RoiNames=[r"Ring_High_Dose",r"Ring_Medium_Dose",r"Ring_Low_Dose"], RemoveHoles3D=False, RemoveSmallContours=True, AreaThreshold=0.1, ReduceMaxNumberOfPointsInContours=False, MaxNumberOfPoints=None, CreateCopyOfRoi=False, ResolveOverlappingContours=False)
        Case.PatientModel.CreateRoi(Name=r"Protection", Color="Orange", Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.RegionsOfInterest[r"Protection"].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [External], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [r"PTV Low Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': 1.5, 'Inferior': 1.5, 'Anterior': 1.5, 'Posterior': 1.5, 'Right': 1.5, 'Left': 1.5 } }, ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
        Case.PatientModel.RegionsOfInterest[r"Protection"].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
    except:
        print("RING existent deja")      
        
    try:
        Case.PatientModel.RegionsOfInterest[r_PTV_HD].DeleteRoi()
        Case.PatientModel.RegionsOfInterest[r_PTV_MD].DeleteRoi()
        Case.PatientModel.RegionsOfInterest[r_PTV_LD].DeleteRoi()
    except:
        print("delete")
        
################################################################################################
################################################################################################
#############  2 PTV ############################################################################
################################################################################################
################################################################################################

if Nombre_de_PTV ==2:
    #########################
    # PTV dosi
    #########################
    #Gap PTV LOw dose: 1.5cm; Md=1cm
    Gap_LD=1.5

    try:
        nom="z_PTV Low Dose "+str(Gap_LD)+"cm"
        color=Case.PatientModel.RegionsOfInterest["PTV Low Dose"].Color
        Case.PatientModel.CreateRoi(Name=nom, Color=color, Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.RegionsOfInterest[nom].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [r"PTV Low Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [r"PTV High Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': Gap_LD, 'Inferior': Gap_LD, 'Anterior': Gap_LD, 'Posterior': Gap_LD, 'Right': Gap_LD, 'Left': Gap_LD } }, ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
        Case.PatientModel.RegionsOfInterest[nom].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")

    except:
        print("PTV dosi existe deja")
    Gap_LD=0.2
    try:
        nom="z_PTV Low Dose"
        color=Case.PatientModel.RegionsOfInterest[r"PTV Low Dose"].Color
        Case.PatientModel.CreateRoi(Name=nom, Color=color, Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.RegionsOfInterest[nom].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [r"PTV Low Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [r"PTV High Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': Gap_LD, 'Inferior': Gap_LD, 'Anterior': Gap_LD, 'Posterior': Gap_LD, 'Right': Gap_LD, 'Left': Gap_LD } }, ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
        Case.PatientModel.RegionsOfInterest[nom].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
    except:
        print("z_PTV dosi existent deja")
		
    Gap_LD=0


    
    try:
        nom="zz_PTV Low Dose"
        color=Case.PatientModel.RegionsOfInterest[r"PTV Low Dose"].Color
        Case.PatientModel.CreateRoi(Name=nom, Color=color, Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.RegionsOfInterest[nom].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [r"PTV Low Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [r"PTV High Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': Gap_LD, 'Inferior': Gap_LD, 'Anterior': Gap_LD, 'Posterior': Gap_LD, 'Right': Gap_LD, 'Left': Gap_LD } }, ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
        Case.PatientModel.RegionsOfInterest[nom].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")

    except:
        print("zz_PTV dosi existent deja")  

    #########################
    # Ring
    #########################
    
     #TEMP_RING:
    try:
        Case.PatientModel.CreateRoi(Name=r"Ring_High_Dose", Color="Red", Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.CreateRoi(Name=r"Ring_Low_Dose", Color="Blue", Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        r_PTV_HD=RING('PTV High Dose',1.5,0.3)
        r_PTV_LD=RING('PTV Low Dose',1.5,0.3)
    except:
        print("temp ring deja existant")   
    
    try:
        Case.PatientModel.CreateRoi(Name=r"zz_PTV Low Dose", Color="Blue", Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.RegionsOfInterest[r"zz_PTV Low Dose"].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [r"PTV Low Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [r"PTV High Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
        Case.PatientModel.RegionsOfInterest[r"zz_PTV Low Dose"].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")

    except:
        print("zz_PTV deja existant")


    try:
        r=ring_ORL_2PTV(r"Ring_High_Dose",r_PTV_HD,r"zz_PTV Low Dose")
        r=ring_ORL_2PTV(r"Ring_Low_Dose",r_PTV_LD,r"Ring_High_Dose")
		
#        Case.PatientModel.StructureSets[Examination].SimplifyContours(RoiNames=[r"Ring_High_Dose",r"Ring_Medium_Dose",r"Ring_Low_Dose"], RemoveHoles3D=False, RemoveSmallContours=True, AreaThreshold=0.1, ReduceMaxNumberOfPointsInContours=False, MaxNumberOfPoints=None, CreateCopyOfRoi=False, ResolveOverlappingContours=False)

        Case.PatientModel.CreateRoi(Name=r"Protection", Color="Orange", Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.RegionsOfInterest[r"Protection"].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [External], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [r"PTV Low Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': 1.5, 'Inferior': 1.5, 'Anterior': 1.5, 'Posterior': 1.5, 'Right': 1.5, 'Left': 1.5 } }, ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
        Case.PatientModel.RegionsOfInterest[r"Protection"].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
    except:
        print("RINGs deja existant")       
        
    try:
        Case.PatientModel.RegionsOfInterest[r_PTV_HD].DeleteRoi()
        Case.PatientModel.RegionsOfInterest[r_PTV_LD].DeleteRoi()
    except:
        print("delete des temp ring")
################################################################################################
################################################################################################
#############  1 PTV ############################################################################
################################################################################################
################################################################################################
if Nombre_de_PTV ==1:
    print("coucou 1 PTV")
    
    #try:
    r=RING(r"PTV High Dose",1.5,0.3)
    print("coucou 2")
    Case.PatientModel.CreateRoi(Name=r"Protection", Color="Orange", Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
    Case.PatientModel.RegionsOfInterest[r"Protection"].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [External], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [r"PTV High Dose"], 'MarginSettings': { 'Type': "Expand", 'Superior': 1.5, 'Inferior': 1.5, 'Anterior': 1.5, 'Posterior': 1.5, 'Right': 1.5, 'Left': 1.5 } }, ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
    Case.PatientModel.RegionsOfInterest[r"Protection"].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
    #except:
    #    print("1 PTV ring deja existant")
    Case.PatientModel.RegionsOfInterest[r"PTV High Dose"].Name = r"PTV"
  
#########################
# z_OAR
#########################


##############
# Creation des z_OAR
#############
if Nombre_de_PTV ==1:
	PTV_inter= "PTV"
else:
	PTV_inter="PTV Low Dose"
	
dict_z_OAR_a_creer ={}
for i,roi in enumerate(OARs):
    Case.PatientModel.CreateRoi(Name=r"inters_OAR", Color="Black", Type="Organ", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
    Case.PatientModel.RegionsOfInterest['inters_OAR'].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [roi], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [PTV_inter], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ResultOperation="Intersection", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
    Case.PatientModel.RegionsOfInterest['inters_OAR'].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
    if Case.PatientModel.StructureSets[Nom_CT_selectionne].RoiGeometries['inters_OAR'].HasContours() is True:
        dict_z_OAR_a_creer[roi]= 0
    else:
        dict_z_OAR_a_creer[roi]=1
    Case.PatientModel.RegionsOfInterest['inters_OAR'].DeleteRoi()



gap=0.2




for roi in dict_z_OAR_a_creer:
    if dict_z_OAR_a_creer[roi]==0:
        print('z_roi a crer:',roi)
        color=Case.PatientModel.RegionsOfInterest[roi].Color
        nom=r"z_"+roi+'_'+PTV_inter+'_gap_'+str(gap)
        Case.PatientModel.CreateRoi(Name=nom, Color=color, Type="undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.RegionsOfInterest[nom].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [roi], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [PTV_inter], 'MarginSettings': { 'Type': "Expand", 'Superior': gap, 'Inferior': gap, 'Anterior': gap, 'Posterior': gap, 'Right': gap, 'Left': gap } }, ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
        Case.PatientModel.RegionsOfInterest[nom].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
