from connect import *
from tkinter import *
import re
import os


def checks_quit_script():
    """ Function aiming to close any pop-up when the red-cross is clicked """
    global quit_script
    if quit_script:
        print('Pop-up was quit by red-cross click -> exiting')
        sys.exit()
    quit_script = True

def select_all_checkboxes():
    for checkbox in exam_dict.values():
        checkbox.set(True)

def unselect_all_checkboxes():
    for checkbox in exam_dict.values():
        checkbox.set(False)

def export_ct(patient, master, patient_id, examination_list, exam_dict, parent_export_path, anonym_settings):
    """ Function exporting CTs checked in the pop up when user clicks on button OK """
    global quit_script
    # Saving patient in order to export
    patient.Save()
    # Create folder for patient (with name = patient ID) in export path if does not exist yet
    patient_export_path = os.path.join(parent_export_path, patient_id)
    patient_folder_exist = os.path.exists(patient_export_path)
    assert not patient_folder_exist, 'Patient folder already exists'
    os.mkdir(patient_export_path)
    for exam in examination_list:
        if exam_dict[exam].get():
            exam_export_path = os.path.join(patient_export_path, exam)
            exam_folder_exist = os.path.exists(exam_export_path)
            assert not exam_folder_exist, 'Exam folder already exists'
            os.mkdir(exam_export_path)
            print(f'Exporting {exam}')
            case.ScriptableDicomExport(ExportFolderPath=exam_export_path, Examinations=[exam],
                                       AnonymizationSettings=anonym_settings, IgnorePreConditionWarnings=False)
    quit_script = False
    master.destroy()

case = get_current('Case')
patient = get_current('Patient')
clinic_db = get_current('ClinicDB')
parent_export_path =r'\\nas-01\PHY_RT\ScreenshotsMedecins\Antonin'

# Anonymisation settings for export
default_anonymization_options = clinic_db.GetSiteSettings().DicomSettings.DefaultAnonymizationOptions
anonymization_settings = {"Anonymize": True,
                          "AnonymizedName": "anonymizedName",
                          "AnonymizedID": "anonymizedID",
                          "RetainDates": default_anonymization_options.RetainLongitudinalTemporalInformationFullDatesOption,
                          "RetainDeviceIdentity": default_anonymization_options.RetainDeviceIdentityOption,
                          "RetainInstitutionIdentity": default_anonymization_options.RetainInstitutionIdentityOption,
                          "RetainUIDs": default_anonymization_options.RetainUIDs,
                          "RetainSafePrivateAttributes": default_anonymization_options.RetainSafePrivateOption}

# Retrieve CT phases in examinations (name should be CT + number)
examinations_list = [exam.Name.strip() for exam in case.Examinations]
ct_phases_exam = []
for exam in examinations_list:
    match = re.search(r'ct \d+', exam.lower())
    if match:
        ct_phases_exam.append(exam)


# Creation of pop up asking which rois to delete to user
quit_script = True
root_pop_up = Tk()

# Dictionary associating every examination to an intVar() tracking the checkbutton state (checked or not) of the pop up
exam_dict = {exam: IntVar() for exam in examinations_list}

root_pop_up.title("Export CT")
Label(root_pop_up, text="Choisir les CTs à exporter :").grid(row=0, column=0, pady=10)

# Creates a checkbutton for each CT and every 5 CT, changes the column to have a nicer layout
max_lines_per_column = 5
for r, exam in enumerate(examinations_list):
    check_button = Checkbutton(root_pop_up, text=exam, variable=exam_dict[exam])
    check_button.grid(row=r % max_lines_per_column + 1, column=r // max_lines_per_column, padx=10, sticky=W)
    # Pre check the checkbutton for every CT that is supposed to be a phase
    if exam in ct_phases_exam:
        exam_dict[exam].set(True)

# Adds buttons that selects/unselects all checkboxes
Button(root_pop_up, text='Tout sélectionner', command=select_all_checkboxes).grid(
    row=max_lines_per_column + 2, column=0, sticky=W, padx=15, pady=5)
Button(root_pop_up, text='Tout désélectionner', command=unselect_all_checkboxes).grid(
    row=max_lines_per_column + 3, column=0, sticky=W, padx=15, pady=3)

# Warn user that patient data will be saved before export
Label(root_pop_up, text='Les données du patient seront sauvegardées avant export.',
      foreground='red', font='Calibri 12 bold').grid(row=max_lines_per_column + 4, column=0, pady=10, padx=10)

# Adds an okay button centered at the bottom of pop up
ok_button_frame = Frame(root_pop_up)
ok_button_frame.grid(row=max_lines_per_column + 5, column=0,
                     columnspan=len(examinations_list) // max_lines_per_column + 2)

onclick_continue_function = lambda: export_ct(patient, root_pop_up, patient.PatientID, examinations_list, exam_dict,
                                              parent_export_path, anonymization_settings)
Button(ok_button_frame, text='OK', command=onclick_continue_function, height=1, width=10).grid(row=0, column=0, pady=10)

root_pop_up.bind('<Return>', lambda event: onclick_continue_function())
root_pop_up.bind('<Escape>', lambda event: sys.exit())
mainloop()
checks_quit_script()

