from connect import *
from tkinter import *
import sys


def checks_quit_script():
    """ Function aiming to close any pop-up when the red-cross is clicked """
    global quit_script
    if quit_script:
        print('Pop-up was quit by red-cross click -> exiting')
        sys.exit()
    quit_script = True


def delete_slices(master, rois_list_names, rois_dict, rois_geom):
    """ Function deleting empty rois checked in the pop up when user clicks on button OK """
    global quit_script
    for roi_name in rois_list_names:
        if rois_dict[roi_name].get():
            print(f'Cutting slice of ROI {roi_name}')
            roi_contours = rois_geom[roi_name].PrimaryShape.Contours
            # Contours are stored in a list (z) of lists of dictionnaries (containing x, y, z)
            # If contours are fragmented (several pieces on the same slice) the fragments are stored in different index
            # of the first list 
            # e.g. roi_contours[0] and roi_contours[1] have the same z because there are fragments of contours on the
            # same slice
            # To begin we retrieve all the z coordinates (without duplicates) that have contours of the ROI considered

            # If the ROI is only on 3 slices => not cuts
            unique_z_coordinates = sorted(
                set([coord['z'] for z_index_coord in roi_contours for coord in z_index_coord]))
            if len(unique_z_coordinates) <= 3:
                cut_contours = roi_contours
            else:
                print("type de unique_z_coordinates")
                print(type(unique_z_coordinates))
                # [:len(unique_z_coordinates) - 1:4] : starts at 0 and goes until last by step of 4
                # [unique_z_coordinates[-1] adds the last slice because we want to keep 1st and last slice contours
                cut_z_coordinates = unique_z_coordinates[:len(unique_z_coordinates) - 1:4] + [unique_z_coordinates[-1]]
                # z_index_coord[0]['z'] : 1st index is 0 because every dictionary in z_index_coord has the same z
                cut_contours = [z_index_coord for z_index_coord in roi_contours if
                                z_index_coord[0]['z'] in cut_z_coordinates]
            rois_geom[roi_name].PrimaryShape.Contours = cut_contours
    quit_script = False
    master.destroy()


case = get_current('Case')
exam = get_current('Examination')
rois_geom = case.PatientModel.StructureSets[exam.Name].RoiGeometries
roi_list = [roi.OfRoi.Name for roi in rois_geom if roi.HasContours()]
rois_list_names = sorted(roi_list, key=lambda string: string.lower())

### Creation of pop up asking which rois to delete to user ###

quit_script = True
root_pop_up = Tk()

# Dictionary associating every empty roi names to an intVar() tracking the checkbutton state (checked or not)
# of the pop up
rois_dict = {roi_name: IntVar() for roi_name in rois_list_names}

root_pop_up.title("Suppression de coupes dans une ROI")
Label(root_pop_up, text="Choisir les ROIs pour lesquelles il faut supprimer des coupes :").grid(row=0, column=0,
                                                                                                padx=10, pady=10)
# Creates a checkbutton for each empty rois names and every 5 empty rois names, changes the column to have a nicer 
# layout
max_lines_per_column = 5
for r, roi_name in enumerate(rois_list_names):
    check_button = Checkbutton(root_pop_up, text=roi_name, variable=rois_dict[roi_name])
    check_button.grid(row=r % max_lines_per_column + 1, column=r // max_lines_per_column, padx=10, sticky=W)


# Adds buttons that selects/unselects all checkboxes
def select_all_checkboxes():
    for checkbox in rois_dict.values():
        checkbox.set(True)


def unselect_all_checkboxes():
    for checkbox in rois_dict.values():
        checkbox.set(False)


Button(root_pop_up, text='Tout sélectionner', command=select_all_checkboxes).grid(
    row=max_lines_per_column + 2, column=0, sticky=W, padx=20, pady=1)
Button(root_pop_up, text='Tout désélectionner', command=unselect_all_checkboxes).grid(
    row=max_lines_per_column + 3, column=0, sticky=W, padx=20)

# Adds an okay button centered at the bottom of pop up
ok_button_frame = Frame(root_pop_up)
ok_button_frame.grid(row=max_lines_per_column + 4, column=0,
                     columnspan=len(rois_list_names) // max_lines_per_column + 2)

onclick_continue_function = lambda: delete_slices(root_pop_up, rois_list_names, rois_dict, rois_geom)
Button(ok_button_frame, text='OK', command=onclick_continue_function, height=1, width=10).grid(row=0, column=0, pady=10)

root_pop_up.bind('<Return>', lambda event: onclick_continue_function())
root_pop_up.bind('<Escape>', lambda event: sys.exit())
mainloop()
checks_quit_script()
