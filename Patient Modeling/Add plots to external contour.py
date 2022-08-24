# Script recorded 22 Dec 2017

#   RayStation version: 6.1.1.2
#   Selected patient: ...

from connect import *

case = get_current("Case")
examination = get_current("Examination")


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



