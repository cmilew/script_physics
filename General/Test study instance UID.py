from connect import *
import tkinter.ttk as ttk
from tkinter import *

case = get_current('Case')
examinations = [exam.Name for exam in case.Examinations]


def checks_quit_script():
    """ Function aiming to close any pop-up when the red-cross is clicked """
    global quit_script
    if quit_script:
        print('Pop-up was quit by red-cross click -> exiting')
        sys.exit()
    quit_script = True


def get_ct(master, scrolling_menu_exam):
    """Function aiming to retrieve the CT chose by the user (should be the CT used for dosimetry) """
    chosen_ct = scrolling_menu_exam.get()
    global ct_dosi_name, quit_script
    if chosen_ct != '':
        ct_dosi_name = chosen_ct
        quit_script = False
        master.destroy()


# Pop up asking for CT to check
quit_script = True
ct_dosi_name = None
root_pop_up = Tk()
root_pop_up.title("Choix du CT")
Label(root_pop_up, text="CT à utiliser pour la dosimétrie :").grid(row=1, column=1, padx=5, pady=5)
scrolling_menu_exam = ttk.Combobox(root_pop_up, values=sorted(examinations), width=17, state='readonly')
scrolling_menu_exam.grid(row=1, column=2, padx=8, pady=5)
onclick_continue_function = lambda: get_ct(root_pop_up, scrolling_menu_exam)
Button(root_pop_up, text='Continuer', command=onclick_continue_function).grid(row=2, column=2, padx=5, pady=5)
root_pop_up.bind('<Return>', lambda event: onclick_continue_function())
root_pop_up.bind('<Escape>', lambda event: sys.exit())
mainloop()
checks_quit_script()

ct_dosi = case.Examinations[ct_dosi_name]
is_study_shadow = False
is_study_instance_uid_corrupted = False

# Study shadow test
try:
    study_shadow_test = ct_dosi.GetStoredDicomTagValueForVerification(Group=0x0008, Element=0x0050)
    print(study_shadow_test)
except:
    is_study_shadow = True


# Study instance UID verification
study_instance_uid = str(ct_dosi.GetStoredDicomTagValueForVerification(Group=0x0020, Element=0x000D))
print("Study instance UID :", study_instance_uid)
# Gets groups separated by '.'
groups = study_instance_uid.split('.')
# if group starts with 0 and is not '.0.', study instance uid is corrupted
is_study_instance_uid_corrupted = any(group.startswith('0') and group != '0' for group in groups)

# Message to display in pop up
if is_study_shadow and is_study_instance_uid_corrupted:
    message = 'Attention le CT "' + ct_dosi_name + '" est un study shadow ET son study Instance UID du CT est ' \
                                                  'corrompu, contactez le physicien de garde (4905).'
elif is_study_shadow and is_study_instance_uid_corrupted == False:
    message = 'Attention, le CT "' + ct_dosi_name + '" est un study shadow, contacter le physicien de garde (4905)'
elif is_study_shadow == False and is_study_instance_uid_corrupted:
    message = 'Attention le Study Instance UID du CT "' + ct_dosi_name + '" est corrompu, contactez le physicien ' \
                                                                        'de garde (4905).'
else:
    message = 'Le CT n\'est pas corrompu, vous pouvez contourer dessus.'

print(message)
root_pop_up = Tk()
root_pop_up.title("")
if is_study_shadow or is_study_instance_uid_corrupted:
    Label(root_pop_up, text=message, foreground='red', font='Calibri 12 bold').grid(row=1, column=1, padx=5, pady=5)
else:
    Label(root_pop_up, text=message).grid(row=1, column=1, padx=5, pady=5)
Button(root_pop_up, text='OK', command=sys.exit, width=10).grid(row=2, column=1, padx=5, pady=5)
root_pop_up.bind('<Return>', lambda event: sys.exit())
root_pop_up.bind('<Escape>', lambda event: sys.exit())
mainloop()
checks_quit_script()
