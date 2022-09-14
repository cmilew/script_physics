# Script recorded 13 Jan 2017

#------------------------------------------------------------------------
#			Lancer 3 processus d'optimisation (de N itérations)
#------------------------------------------------------------------------
#
#Création : 
#13/01/2017 - M. Edouard
#
#Modication :
#30/07/2020 - A. Alexis - V2.0 - RS9B
#			  *Refonte du code qui était basé sur le beam_set.Number unique au moment de la création d'un beam set
#			   utilisé pour atteindre les PlanOptimizations, ce qui pouvait amener à lancer 3 processus d'optimisations
#			   pour un beam set dans lequel l'utilisateur ne se trouvait pas. Cela se produisait lorsque
#			   un beam set avait été crée (beam_set.Number=1) puis avait été supprimé. Ainsi, le 1er beam set visible
#			   présentait le beam_set.Number = 2 et cela induisait l'erreur évoquée plus haut.
#
#
#20/10/2020 - A. Alexis - V2.1 - RS9B
#			  *Ajout de la vérification de la compatibilité du sens de rotation des arcs avec les angles de départ et d'arrivée.
#			  (Clockwise : 181 -> 179 en passant par 0 ; CounterClockwise : 179 -> 181 en passant par 0)
#			  *Ajout de la vérification de l'alternance du sens de rotation des arcs
#
#10/11/2020 - J. Vautier - 2.2 - RS9B
#                     *Ajout de la vérification de la présence du tag (0008,0050). En cas d'absence de ce tag, il s'agit d'un study shadow. L'optimisation n'est pas lancée.
#
#
#
#
#
#----------------------------------------------------------------



from connect import *
import sys
from tkinter import *
import tkinter.messagebox


patient=get_current('Patient')
exam = get_current("Examination")

patient.Save()



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
    study_shadow_test = exam.GetStoredDicomTagValueForVerification(Group=0x0008, Element=0x0050)
    print(study_shadow_test)
except:
    is_study_shadow = True

# Study instance UID verification
study_instance_uid = str(exam.GetStoredDicomTagValueForVerification(Group=0x0020, Element=0x000D))
# Gets groups separated by '.'
groups = study_instance_uid.split('.')
# if group starts with 0 and is not '.0.', study instance uid is corrupted
is_study_instance_uid_corrupted = any(group.startswith('0') and group != '0' for group in groups)

# Message to display in pop up
if is_study_shadow and is_study_instance_uid_corrupted:
    message = 'Attention le CT "' + exam.Name + '" est un study shadow ET son study Instance UID du CT est ' \
                                                  'corrompu, contactez le physicien de garde (4905).'
elif is_study_shadow and is_study_instance_uid_corrupted == False:
    message = 'Attention, le CT "' + exam.Name + '" est un study shadow, contacter le physicien de garde (4905)'
elif is_study_shadow == False and is_study_instance_uid_corrupted:
    message = 'Attention le Study Instance UID du CT "' + exam.Name + '" est corrompu, contactez le physicien ' \
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


plan = get_current("Plan")
beam_set = get_current("BeamSet")
beam_set.SetCurrent()


#Nom du beam set
beam_set_name = beam_set.DicomPlanLabel
#Nombre de plans optimisés (=nb de beam sets ici)
number_of_planopti = plan.PlanOptimizations.Count

#Vérification du sens de rotation du bras en fonction des angles de départ et d'arrivée. Définition propre à l'IGR (VERSA HD et NOVALIS).
N_beams=beam_set.Beams.Count
print("N beams =",N_beams)
for z in range(N_beams):
	if beam_set.Beams[z].ArcRotationDirection == 'Clockwise':
		#Angle de départ : droite patient
		if beam_set.Beams[z].GantryAngle >= 181 and beam_set.Beams[z].GantryAngle < 360:
			if (beam_set.Beams[z].ArcStopGantryAngle >= beam_set.Beams[z].GantryAngle) or (beam_set.Beams[z].ArcStopGantryAngle >= 0 and beam_set.Beams[z].ArcStopGantryAngle <= 179):
				print("Sens de rotation du bras pour l'arc ",z," est ok.CW 1.")
			else:
				top=Tk()
				top.withdraw()
				tkinter.messagebox.showerror("Information" , "Il y a un problème dans la définition des angles de départ et d'arrivée de l'arc "+beam_set.Beams[z].Name+ \
				" (Start Angle = "+str(beam_set.Beams[z].GantryAngle)+" ; Stop Angle = "+str(beam_set.Beams[z].ArcStopGantryAngle)+" ; Direction = "+ \
				str(beam_set.Beams[z].ArcRotationDirection)+" )")
				sys.exit()
		#Angle de départ : gauche patient
		elif beam_set.Beams[z].GantryAngle >= 0 and beam_set.Beams[z].GantryAngle <= 179:
			if (beam_set.Beams[z].ArcStopGantryAngle >= beam_set.Beams[z].GantryAngle) and (beam_set.Beams[z].ArcStopGantryAngle <= 179):
				print("Sens de rotation du bras pour l'arc ",z," est ok. CW 2.")
			else:
				top=Tk()
				top.withdraw()
				tkinter.messagebox.showerror("Information" , "Il y a un problème dans la définition des angles de départ et d'arrivée de l'arc "+beam_set.Beams[z].Name+ \
				" (Start Angle = "+str(beam_set.Beams[z].GantryAngle)+" ; Stop Angle = "+str(beam_set.Beams[z].ArcStopGantryAngle)+" ; Direction = "+ \
				str(beam_set.Beams[z].ArcRotationDirection)+" )")
				sys.exit()
	elif beam_set.Beams[z].ArcRotationDirection == 'CounterClockwise':
		#Angle de départ : gauche patient
		if beam_set.Beams[z].GantryAngle <= 179 and beam_set.Beams[z].GantryAngle >= 0:
			if (beam_set.Beams[z].ArcStopGantryAngle <= beam_set.Beams[z].GantryAngle) or (beam_set.Beams[z].ArcStopGantryAngle < 360 and beam_set.Beams[z].ArcStopGantryAngle >= 181):
				print("Sens de rotation du bras pour l'arc ",z," est ok. CounterClockwise 1.")
			else:
				top=Tk()
				top.withdraw()
				tkinter.messagebox.showerror("Information" , "Il y a un problème dans la définition des angles de départ et d'arrivée de l'arc "+beam_set.Beams[z].Name+ \
				" (Start Angle = "+str(beam_set.Beams[z].GantryAngle)+" ; Stop Angle = "+str(beam_set.Beams[z].ArcStopGantryAngle)+" ; Direction = "+ \
				str(beam_set.Beams[z].ArcRotationDirection)+" )")
				sys.exit()
		#Angle de départ : droite patient
		elif beam_set.Beams[z].GantryAngle < 360 and beam_set.Beams[z].GantryAngle >= 181:
			if (beam_set.Beams[z].ArcStopGantryAngle < beam_set.Beams[z].GantryAngle) and (beam_set.Beams[z].ArcStopGantryAngle >= 181):
				print("Sens de rotation du bras pour l'arc ",z," est ok. CounterClockwise 2.")
			else:
				top=Tk()
				top.withdraw()
				tkinter.messagebox.showerror("Information" , "Il y a un problème dans la définition des angles de départ et d'arrivée de l'arc "+beam_set.Beams[z].Name+ \
				" (Start Angle = "+str(beam_set.Beams[z].GantryAngle)+" ; Stop Angle = "+str(beam_set.Beams[z].ArcStopGantryAngle)+" ; Direction = "+ \
				str(beam_set.Beams[z].ArcRotationDirection)+" )")
				sys.exit()

#Vérification de l'alternance de la direction des arcs
for z in range(N_beams):
	print("z=",z)
	if z==0:
		print('ok')
	else:
		if (beam_set.Beams[z-1].ArcRotationDirection == "Clockwise" and beam_set.Beams[z].ArcRotationDirection == "CounterClockwise") or (beam_set.Beams[z-1].ArcRotationDirection == "CounterClockwise" and beam_set.Beams[z].ArcRotationDirection == "Clockwise"):
			print(z)
		else:
			top=Tk()
			top.withdraw()
			tkinter.messagebox.showerror("Information" , "Il y a un problème dans la définition de directions des arcs. Les arcs "+beam_set.Beams[z-1].Name+ \
			" et "+beam_set.Beams[z].Name+" ont la même direction ("+beam_set.Beams[z].ArcRotationDirection+").")


#Lancement de 3 processus d'optimisation du plan/beam set dans lequel l'utilisateur se trouve dans RS
for k in range(number_of_planopti):
	#On vérifie que le plan à optimiser correspond bien à celui du beam set dans lequel l'utilisateur se trouve
	if beam_set_name == plan.PlanOptimizations[k].OptimizedBeamSets[0].DicomPlanLabel:
		#3 processus d'optimisation
		for idx in range(3):
			plan.PlanOptimizations[k].RunOptimization()
		break








