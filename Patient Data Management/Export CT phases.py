from connect import *
from tkinter import *
import tkinter.ttk as ttk
import os
import re


def checks_quit_script():
    """ Function aiming to close any pop-up when the red-cross is clicked """
    global quit_script
    if quit_script:
        print('Pop-up was quit by red-cross click -> exiting')
        sys.exit()
    quit_script = True

def continue_script(master):
    global quit_script
    quit_script = False
    master.destroy()


def get_entry(master, scrolling_menu_ct, ct_type, exam_to_export, examinations_list):
    entry_ct_value = scrolling_menu_ct.get()
    if entry_ct_value != '':
        entry_ct_value = re.search(r'(.*) réalisé le (.*) - (.*)', entry_ct_value)
        selected_ct_name = entry_ct_value.group(1)
        selected_ct_date_time = entry_ct_value.group(2)
        selected_examination = [examination.Name for examination in examinations_list if examination.Name == selected_ct_name
                                and str(examination.GetExaminationDateTime()) == selected_ct_date_time]
        assert len(selected_examination) != 0, 'Found no associated examination with selected name: should not happen'
        assert len(selected_examination) < 2, 'Found multiple examinations with selected name: should not happen'
        exam_to_export[ct_type] = [selected_examination[0]]
    else:
        return
    global quit_script
    quit_script = False
    master.destroy()


case = get_current('Case')
patient = get_current('Patient')
clinic_db = get_current('ClinicDB')
# parent_export_path = r'\\nas-01\PHY_PROC\RepertoirePhysiciens\Candice MILEWSKI\ct'
parent_export_path =r'\\nas-01\PHY_RT\ScreenshotsMedecins\Antonin'

# Creates a dictionnary containing in keys the type of CT that should be export (MaxIP, average, CT_10 for phase 10%...)
# and in values the name given in RayStation of the CT with this type
# Gets the type of the CT in RS from the series description tag
examinations_list = case.Examinations
exam_to_export = {'MaxIP': [], 'CTAIP': [], 'CT_0': [], 'CT_10': [], 'CT_20': [], 'CT_30': [], 'CT_40': [], 'CT_50': [],
                  'CT_60': [], 'CT_70': [], 'CT_80': [], 'CT_90': []}
for exam in examinations_list:
    exam_data = exam.GetAcquisitionDataFromDicom()
    serie_description = exam_data['SeriesModule']['SeriesDescription']
    if serie_description != None:
        if 'MaxIP' in serie_description:
            exam_to_export['MaxIP'].append(exam.Name)
        elif 'Average CT' in serie_description:
            exam_to_export['CTAIP'].append(exam.Name)
        elif serie_description.endswith('%'):
            index = len(serie_description) - 2
            phase_number = serie_description[index]
            for key in exam_to_export.keys():
                if key[3] == phase_number:
                    exam_to_export[key].append(exam.Name)
                    break

# If multiple CT of the same type have been found : pop up to warn user and ask him to choose which one to export with
# scrolling menu
# If no CT found for one of the type, stores it in a list
exam_not_found = []
for key in exam_to_export.keys():
    if len(exam_to_export[key]) > 1:
        selected_ct_value = None
        quit_script = True
        root_pop_up = Tk()
        root_pop_up.title("Plusieurs CTs trouvés")
        text = 'Plusieurs CTs  \"' + key + '\"  ont été trouvés. Choisir le CT  \"' + key +'\" à exporter :'
        Label(root_pop_up, text=text).grid(row=0, column=0, pady=10, padx=10)
        scrolling_menu_examinations = []
        for exam in exam_to_export[key]:
            exam_data = examinations_list[exam].GetAcquisitionDataFromDicom()
            serie_description = exam_data['SeriesModule']['SeriesDescription']
            label = f'{exam} réalisé le {examinations_list[exam].GetExaminationDateTime()} - {serie_description}'
            scrolling_menu_examinations.append(label)
        scrolling_menu_ct = ttk.Combobox(root_pop_up, values=scrolling_menu_examinations, width=100,
                                               state='readonly')
        scrolling_menu_ct.grid(row=2, column=0, sticky=W, padx=10)
        onclick_continue_function = lambda: get_entry(root_pop_up, scrolling_menu_ct, key, exam_to_export,
                                                      examinations_list)
        Button(root_pop_up, text='Continuer', command=onclick_continue_function).grid(row=11, column=2, sticky=W,
                                                                                      pady=4, padx=10)
        root_pop_up.bind('<Return>', lambda event: onclick_continue_function())
        root_pop_up.bind('<Escape>', lambda event: sys.exit())
        mainloop()
        checks_quit_script()
    elif len(exam_to_export[key]) == 0:
        exam_not_found.append(key)

# If no CT of one of the type required has been found, remove it from the dict of CT to export and warn user with pop up
for exam in exam_not_found:
    del exam_to_export[exam]
if len(exam_not_found) > 0:
    quit_script = True
    root_pop_up = Tk()
    root_pop_up.title("CT(s) manquant(s)")
    Label(root_pop_up, text='Le/les CT(s) suivant n\'ont pas été trouvé(s) et ne seront donc pas exportés '
                            ':').grid(row=0, column=0, padx=10)
    row = 1
    for exam in exam_not_found:
        Label(root_pop_up, text=exam).grid(row=row, column=0, pady=2)
        row += 1
    onclick_continue_script = lambda: continue_script(root_pop_up)
    Button(root_pop_up, text='OK', command=onclick_continue_script, width = 15).grid(row=row+1, column=0, pady=4)
    root_pop_up.bind('<Return>', lambda event: onclick_continue_function())
    root_pop_up.bind('<Escape>', lambda event: sys.exit())
    mainloop()
    checks_quit_script()

# Saving patient in order to export
patient.Save()

# Create folder for patient (with name = patient ID) in export path if does not exist yet
patient_export_path = os.path.join(parent_export_path, patient.PatientID)
patient_folder_exist = os.path.exists(patient_export_path)
assert not patient_folder_exist, 'Patient folder already exists'
os.mkdir(patient_export_path)

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

# CT export
for ct_type in exam_to_export.keys():
    # In patient folder, creates a folder with CT type as name if does not already exist
    exam_export_path = os.path.join(patient_export_path, ct_type)
    exam_folder_exist = os.path.exists(exam_export_path)
    assert not exam_folder_exist, 'Exam folder already exists'
    os.mkdir(exam_export_path)
    print(f'Exporting {exam_to_export[ct_type]}')
    case.ScriptableDicomExport(ExportFolderPath=exam_export_path, Examinations=exam_to_export[ct_type],
                               AnonymizationSettings=anonymization_settings, IgnorePreConditionWarnings=False)
