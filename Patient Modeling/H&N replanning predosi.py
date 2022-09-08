from connect import *
# -*- coding: utf-8 -*-
from tkinter import*


try:
	Case=get_current('Case')
	Examination=get_current('Examination')
except:
	print('No case / examination selected')
	
	

Nom_CT_selectionne=Examination.Name

#copier/coller les geometries et supprimer

roi_geometries=Case.PatientModel.StructureSets[Nom_CT_selectionne].RoiGeometries
'''
rois_a_modifier=['CTV High Dose','CTV Medium Dose','CTV Low Dose','PTV High Dose','PTV Medium Dose','PTV Low Dose']

for roi in rois_a_modifier:
	Case.PatientModel.RegionsOfInterest[roi+"_1"].Name = roi
	
'''
PTVs=[]
for roi in roi_geometries:
    if Case.PatientModel.RegionsOfInterest[roi.OfRoi.Name].Type =='External':
        External=roi.OfRoi.Name
    if Case.PatientModel.RegionsOfInterest[roi.OfRoi.Name].Type =='Ptv':
        PTVs.append(roi.OfRoi.Name)
print("PTVs:",PTVs)
Nombre_de_PTV=len(PTVs)
print('Le nombre de PTV est :',Nombre_de_PTV)


def ring_ORL_2PTV(ring_name,r_ring,zz_a):
    #Case.PatientModel.CreateRoi(Name=ring_name, Color="Red", Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
    Case.PatientModel.RegionsOfInterest[ring_name].SetAlgebraExpression(ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [r_ring], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [zz_a], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ResultOperation="Subtraction", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
    Case.PatientModel.RegionsOfInterest[ring_name].UpdateDerivedGeometry(Examination=Examination, Algorithm="Auto")
    #Case.PatientModel.StructureSets[Examination].SimplifyContours(RoiNames=[ring_name], RemoveHoles3D=False, RemoveSmallContours=True, AreaThreshold=0.1, ReduceMaxNumberOfPointsInContours=False, MaxNumberOfPoints=None, CreateCopyOfRoi=False, ResolveOverlappingContours=False)

    return True

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
if Nombre_de_PTV==3:
    #########################
    # Ring
    #########################
    rois_a_modifier=['Ring_High_Dose','Ring_Medium_Dose','Ring_Low_Dose']
    for roi in rois_a_modifier:
        try:
            Case.PatientModel.RegionsOfInterest[roi].Name = roi+"_1"
        except:
            print("roi ", roi, " n'existe pas")

    #TEMP_RING:
    
    try:
        Case.PatientModel.CreateRoi(Name=r"Ring_High_Dose", Color="Red", Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.CreateRoi(Name=r"Ring_Medium_Dose", Color="Green", Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
        Case.PatientModel.CreateRoi(Name=r"Ring_Low_Dose", Color="Blue", Type="Undefined", TissueName=None, RbeCellTypeName=None, RoiMaterial=None)
    except:
        print("TEMP RING existent deja") 
		
    try:
        r_PTV_HD=RING('PTV High Dose',1.5,0.3)
        r_PTV_MD=RING('PTV Medium Dose',1.5,0.3)
        r_PTV_LD=RING('PTV Low Dose',1.5,0.3)
    except:
        print("TEMP RING 2 existent deja")
    


    try:
        r=ring_ORL_3PTV(r"Ring_High_Dose",r_PTV_HD,r"zz_PTV Low Dose",r"zz_PTV Medium Dose")
        r=ring_ORL_3PTV(r"Ring_Medium_Dose",r_PTV_MD,r"zz_PTV Low Dose",r"Ring_High_Dose")
        r=ring_ORL_3PTV(r"Ring_Low_Dose",r_PTV_LD,r"Ring_Medium_Dose",r"Ring_High_Dose")
		

    except:
        print("RING existent deja")      
        
    try:
        Case.PatientModel.RegionsOfInterest[r_PTV_HD].DeleteRoi()
        Case.PatientModel.RegionsOfInterest[r_PTV_MD].DeleteRoi()
        Case.PatientModel.RegionsOfInterest[r_PTV_LD].DeleteRoi()
    except:
        print("delete")
	
		
		
if Nombre_de_PTV==2:
    #########################
    # Ring
    #########################
    rois_a_modifier=['Ring_High_Dose','Ring_Low_Dose']
    for roi in rois_a_modifier:
        try:
            Case.PatientModel.RegionsOfInterest[roi].Name = roi+"_1"
        except:
            print("roi ", roi, " n'existe pas")
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


for roi in rois_a_modifier:
	try:			
		Case.PatientModel.RegionsOfInterest[roi+"_1"].CreateAlgebraGeometry(Examination=Examination, Algorithm="Auto", ExpressionA={ 'Operation': "Union", 'SourceRoiNames': [roi], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ExpressionB={ 'Operation': "Union", 'SourceRoiNames': [], 'MarginSettings': { 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 } }, ResultOperation="None", ResultMarginSettings={ 'Type': "Expand", 'Superior': 0, 'Inferior': 0, 'Anterior': 0, 'Posterior': 0, 'Right': 0, 'Left': 0 })
		Case.PatientModel.RegionsOfInterest[roi].DeleteRoi()
		Case.PatientModel.RegionsOfInterest[roi+"_1"].Name=roi
	except:
		print("roi ", roi, " n'existe pas")


