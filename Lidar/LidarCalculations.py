import numpy as np
import json
import matplotlib.pyplot as plt
import seaborn as sns
from math import cos, sin, sqrt, atan
from sklearn.neighbors import NearestNeighbors


file_nb = 0
path_to_output_lidar_file= f'Log/outputLidarFile{file_nb}.csv'
path_to_output_objects_file= f'Log/outputObjectsFile{file_nb}.csv'

verbose = 2
# dictionnary of hyper and other parameters
# structure detailed below
"""lidar_kwargs = {
    # hyper parameters : vine grid description and calculation precision
    'plot_name' : name of the plot
    'bin_size' : 10, # cm, represents the precision for object grouping
    'expected_width' : 200, # cm, the space between two rows of vines
    'expected_distance' : 80, # cm, the space between to neighbor vines within each row
    #other parameters
    'suppress_obj_distance' : 10000, # mm, objects exceeding this distance are deleted from data
    # the following distances and sizes are used to filter objects
    'max_object_size' : 150,  # eliminate too big (mm)
    'min_object_size' : 10, # eliminate too tiny (mm)
    'min_object_distance' : 200, # eliminate too close (mm)
    'max_object_distance' : 7000, # eliminate too far (mm)
    # the following parameters are used to filter objects by density
    'max_nb_obj' : 3, # maximum allowed nb of objects (including self)
    'nbr_range' : 200 # within this distance (mm)
}"""
# loading from robotID.json
with open('robotID.json') as jsonFile:
    data = json.load(jsonFile)
lidar_kwargs = data['lidar']['lidar_kwargs']
plot_name = lidar_kwargs['plot_name'] # numéro de cadastre de la parcelle

def process_lidar_file_to_landmarks(path_to_output_objects_file, kwargs, verbose=0):

    """ This function returns :
    landmarks (list), best_angle (float), distance_to_lidar
    from a csv Lidar Objects File located in path_to_output_objects_file
    csv format : object number, begin_angle, begin_distance, end_angle, end_distance"""

    bin_size = kwargs['bin_size']
    expected_width = kwargs['expected_width']
    expected_distance = kwargs['expected_distance']
    suppress_obj_distance = kwargs['suppress_obj_distance']
    max_object_size = kwargs['max_object_size']
    min_object_size = kwargs['min_object_size']
    min_object_distance = kwargs['min_object_distance']
    max_object_distance = kwargs['max_object_distance']
    max_nb_obj = kwargs['max_nb_obj']
    nbr_range = kwargs['nbr_range']

    # load csv object file
    lidar_objects = np.loadtxt(path_to_output_objects_file, delimiter=",", dtype=float)
    # suppress objects whose distance from Lidar exceeds suppress_obj_distance
    lidar_objects = [obj for obj in lidar_objects if sqrt(obj[2]**2+obj[4]**2)<suppress_obj_distance]
    # creates XY_size list
    objects_XY = to_XY(lidar_objects)
    object_XYsize = to_XYsize(objects_XY)
#    object_XYsize = size_filter(object_XYsize, min_object_size = 10, max_object_size = 200)
    # apply size and distance filter
    filtered_object_XYsize = size_distance_filter(object_XYsize,
                             max_object_size = max_object_size,  # eliminate too big (mm)
                             min_object_size = min_object_size, # eliminate too tiny (mm)
                             min_object_distance = min_object_distance, # eliminate too close (mm)
                             max_object_distance = max_object_distance, # eliminate too far (mm)
                             verbose = verbose)
    # apply density filter
    object_XYsize_reduced = density_filter(filtered_object_XYsize,
                                           max_nb_obj = max_nb_obj,
                                           nbr_range = nbr_range,
                                           verbose=verbose)
    # get vine rows angle
    best_angle, nb_detected_points, distance_to_lidar = get_best_angle(object_XYsize_reduced,
                                                                   bin_size=bin_size,
                                                                   expected_width=expected_width,
                                                                   verbose=verbose)
    # get landmarks
    landmark_object_XYsize, landmark_list = get_landmarks(object_XYsize_reduced, best_angle, distance_to_lidar,
                                                     bin_size=bin_size,
                                                     expected_width=expected_width,
                                                     verbose=verbose)
    # certify landmarks
    landmark_object_XYsize = certify_landmarks(landmark_object_XYsize, landmark_list, best_angle,
                                               expected_distance=expected_distance,
                                               verbose=verbose)
    # get aligned landmark list
    landmarks = grid_align(landmark_object_XYsize, best_angle, distance_to_lidar, expected_width)
    # plot aligned landmarks
    if verbose == 2:
        plt.figure(figsize=(10,10))
        sns.scatterplot(x=landmarks[:,1],y=landmarks[:,2], hue=landmarks[:,4], size=landmarks[:,4])
        plt.grid()
        plt.title(f'landmarks from file : {path_to_output_objects_file}')
        plt.show();

    return landmarks, best_angle, distance_to_lidar

# PRELIMINARY FUNCTIONS

def to_XY(lidar_objects):
    """ returns a list of objects with (x,y) coordinates from a list of (angle, distance) coordinates
    list angle/distance format : object number, angle start (deg), distance start (mm), angle end, distance end
    output format : obj_nb,x1,y1,x2,y2 with 1 = beginning of objet and 2 = end"""
    pi = np.pi
    objects_XY = []
    for object_nb in range(len(lidar_objects)):
        x1 = lidar_objects[object_nb][2]*cos(lidar_objects[object_nb][1]*2*np.pi/360)
        y1 = lidar_objects[object_nb][2]*sin(lidar_objects[object_nb][1]*2*np.pi/360)
        x2 = lidar_objects[object_nb][4]*cos(lidar_objects[object_nb][3]*2*np.pi/360)
        y2 = lidar_objects[object_nb][4]*sin(lidar_objects[object_nb][3]*2*np.pi/360)
        objects_XY.append([object_nb,x1,y1,x2,y2])
    objects_XY = np.asarray(objects_XY)
    return objects_XY

def to_XYsize(objects_list):
    """ returns a list of object centers and size (obj_nb, x, y, size) from a list of (obj_nb,x1,y1,x2,y2) objects"""
    objects_XYsize = []
    for object_nb in range(len(objects_list)):
        size = sqrt((objects_list[object_nb][1]-objects_list[object_nb][3])**2
                    +(objects_list[object_nb][2]-objects_list[object_nb][4])**2)
        objects_XYsize.append([object_nb,(objects_list[object_nb][1]+objects_list[object_nb][3])/2,
                               (objects_list[object_nb][2]+objects_list[object_nb][4])/2, size])
    objects_XYsize = np.asarray(objects_XYsize)
    return objects_XYsize

def size_distance_filter(object_XYsize,
                         max_object_size = 150,  # eliminate too big (mm)
                         min_object_size = 10, # eliminate too tiny (mm)
                         min_object_distance = 200, # eliminate too close (mm)
                         max_object_distance = 7000, # eliminate too far (mm)
                         verbose = 1):
    """returns a list of objects of format XYsize that are filtered by size and distance"""
    filtered_object_XYsize = [list_row for list_row in object_XYsize
                              if list_row[3] < max_object_size
                              and list_row[3] > min_object_size
                              and sqrt(list_row[1]**2+list_row[2]**2)>min_object_distance
                              and sqrt(list_row[1]**2+list_row[2]**2)<max_object_distance]
    if verbose >= 1:
        print(f'{int(len(object_XYsize)-len(filtered_object_XYsize))} objects suppressed by size and distance filter')
        print(f'{len(filtered_object_XYsize)} remaining objects')
    filtered_object_XYsize = np.asarray(filtered_object_XYsize)
    return filtered_object_XYsize

def size_filter(object_XYsize,
                         max_object_size = 150,  # eliminate too big (mm)
                         min_object_size = 10, # eliminate too tiny (mm)
                         verbose = 1):
    """returns a list of objects of format XYsize that are filtered by size """
    filtered_object_XYsize = [list_row for list_row in object_XYsize
                              if list_row[3] < max_object_size
                              and list_row[3] > min_object_size]
    if verbose >= 1:
        print(f'{int(len(object_XYsize)-len(filtered_object_XYsize))} objects suppressed by size filter')
        print(f'{len(filtered_object_XYsize)} remaining objects')
    filtered_object_XYsize = np.asarray(filtered_object_XYsize)
    return filtered_object_XYsize

def density_filter(objects_XYsize, max_nb_obj=3, nbr_range=200, verbose=1):  # maximum number of neighbors in nbr_range (mm)
    """ returns a list of object in format XYsize that have at least max_nb_obj neighbors within a distance of nbr_range """
    density_list = []
    for object_nb in range(len(objects_XYsize)):
        density =0
        for index_nb in range(len(objects_XYsize)):
            distance = (objects_XYsize[object_nb][1]-objects_XYsize[index_nb][1])**2
            distance += (objects_XYsize[object_nb][2]-objects_XYsize[index_nb][2])**2
            distance = sqrt(distance)
            if distance < nbr_range:
                density += 1
        if density >= max_nb_obj:
            density_list.append(objects_XYsize[object_nb][0])
    object_XYsize_reduced = [obj for obj in objects_XYsize if obj[0] not in density_list]
    object_XYsize_reduced = np.asarray(object_XYsize_reduced)
    if verbose >=1:
        print(f'{len(density_list)} objects suppressed by density filter')
        print(f'{len(object_XYsize_reduced)} remaining objects')
    return object_XYsize_reduced

# calculation of vine row direction (best_angle)
# bin_size (default=10) in cm, to group projections, must divide expected_width (use 10, 20 or 40)
# expected_width (default=200) in cm, corridor space between vines [inter-rang]
def get_best_angle(object_XYsize, bin_size=10, expected_width=200, verbose=1):
    """ returns best_angle, nb_detected_point, distance_to_lidar"""
    best_angle = 0
    nb_detected_points = 0
    distance_to_lidar = 0 # (this distance is caluclated modulo expected_width)

    # scan through 180°
    for radar_angle in range(90,270): # angle to which the radar is pointing. The projected line has an angle of radar_angle + pi/2.
        radar_angle_rad = radar_angle *2*np.pi/360
        projected_hist = np.zeros(expected_width) # projection on projected line
        for object_nb in range(len(object_XYsize)):
            #distance = sqrt(filtered_object_XYsize[object_nb][1]**2+filtered_object_XYsize[object_nb][2]**2)
            projection = object_XYsize[object_nb][1]*sin(radar_angle_rad)-object_XYsize[object_nb][2]*cos(radar_angle_rad)
            # group by bins of bin_size
            projection = int(np.round(projection/10/bin_size, decimals=0)*bin_size)
            # group by expected_width
#            if projection>=0 and projection<expected_width: # keep only close elements, try to isolate two nearest vine rows
#                projected_hist[projection] += 1
#            elif projection>-expected_width and projection<0:
#                projected_hist[projection+200] += 1
            projected_hist[projection % expected_width] +=1

        if max(projected_hist) > nb_detected_points:
            best_angle = radar_angle
            nb_detected_points = max(projected_hist)
            distance_to_lidar = np.argmax(projected_hist)

    # check if best_angle +/- 0.5° is better than best_angle
    best_angle2 = best_angle
    for radar_angle in [-0.5, 0.5]: # angle to which the radar is pointing. The projected line has an angle of radar_angle + pi/2.
        radar_angle_rad = (best_angle2 + radar_angle) *2*np.pi/360
        projected_hist = np.zeros(expected_width) # projection on projected line
        for object_nb in range(len(object_XYsize)):
            #distance = sqrt(filtered_object_XYsize[object_nb][1]**2+filtered_object_XYsize[object_nb][2]**2)
            projection = object_XYsize[object_nb][1]*sin(radar_angle_rad)-object_XYsize[object_nb][2]*cos(radar_angle_rad)
            # group by bins of bin_size
            projection = int(np.round(projection/10/bin_size, decimals=0)*bin_size)
            # group by expected_width
            projected_hist[projection % expected_width] +=1
        if max(projected_hist) > nb_detected_points:
            best_angle = (best_angle2 + radar_angle)
            nb_detected_points = max(projected_hist)
            distance_to_lidar = np.argmax(projected_hist)
    if verbose >= 1:
        print(f'angle = {best_angle}, nb detected points = {int(nb_detected_points)}, distance to lidar (cm) = {distance_to_lidar}')

    if verbose >= 2:
        # draw density function
        radar_angle_rad = best_angle *2*np.pi/360
        projected_hist = np.zeros(expected_width) # projection on projected line
        for object_nb in range(len(object_XYsize)):
            #distance = sqrt(filtered_object_XYsize[object_nb][1]**2+filtered_object_XYsize[object_nb][2]**2)
            projection = object_XYsize[object_nb][1]*sin(radar_angle_rad)-object_XYsize[object_nb][2]*cos(radar_angle_rad)
            # group by bins of bin_size
            projection = int(np.round(projection/10/bin_size, decimals=0)*bin_size)
            # group by expected_width
            projected_hist[projection % expected_width] +=1
        plt.plot(projected_hist)
        plt.show();

    return best_angle, nb_detected_points, distance_to_lidar # (distance in cm)

# function to get coordinates of landmarks
# equations of nearby landmark lines (distance_to_lidar +-n.expected_width) :
# y = x.tan(alpha) + (distance_of_max +-n.expected_width)/cos(alpha)
# landmark_list returns object_nb in object_XYsize list and n
def get_landmarks(object_XYsize, angle, distance_to_lidar, bin_size, expected_width, verbose=1):
    """ returns a list of (object_nb, projected distance modulo expected_width [inter-rang]) """
    #object_XYsize=size_distance_filter(object_XYsize)
    landmark_list = []
    angle_rad = angle *2*np.pi/360
    for object_nb in range(len(object_XYsize)):
        projection = object_XYsize[object_nb][1]*sin(angle_rad)-object_XYsize[object_nb][2]*cos(angle_rad)
        projection = int(np.round(projection/10/bin_size, decimals=0)*bin_size) # from mm to cm (/10)
        if projection % expected_width == distance_to_lidar:
            landmark_list.append([object_XYsize[object_nb][0], projection//expected_width])
    landmark_list = np.asarray(landmark_list)
    landmark_object_XYsize = [list_row for list_row in object_XYsize
                              if list_row[0] in landmark_list[:,0]]
    landmark_object_XYsize = np.asarray(landmark_object_XYsize)
    if verbose >=1:
        print(f'found {len(landmark_object_XYsize)} potential landmarks')
    return landmark_object_XYsize, landmark_list

def certify_landmarks(landmark_object_XYsize, landmark_list, best_angle, expected_distance = 80, bin_size = 10, verbose=1):
    """
    returns an augmented landmark_object_XYsize list
    applys a grade to landmarks belonging to a grid
    applys a grade to objects regularily spaced (see expected_distance below)
    a new column is added to object_list (containing the grade of each landmark)
    list structure becomes : number, x, y size, grade

    expected_distance = distance between vines within a row
    (vines are planted every expected_distance)
    """

    # certifying landmarks (1)
    # isolate points that belong to a grid (this garanties these points are landmarks):
    # they are in line, let's now check the projection accross rows and see if they match with another point from another row
    angle_rad = best_angle *2*np.pi/360
    projected_hist = np.zeros(2000) # projection on vine line, 1.000 means 10.000 mm = 10m
    landmark_label_list=[]
    for object_nb in range(len(landmark_object_XYsize)):
        projection = landmark_object_XYsize[object_nb][1]*cos(angle_rad)+landmark_object_XYsize[object_nb][2]*sin(angle_rad)
        # group by bins of bin_size
        projection = int(np.round(projection/10/bin_size, decimals=0)*bin_size)
        if projection>-1000 and projection<1000:
            projected_hist[projection+1000] += 1
    for object_nb in range(len(landmark_object_XYsize)):
        projection = landmark_object_XYsize[object_nb][1]*cos(angle_rad)+landmark_object_XYsize[object_nb][2]*sin(angle_rad)
        projection = int(np.round(projection/10/bin_size, decimals=0)*bin_size)
        if projected_hist[projection+1000]>1:
            landmark_label_list.append(1)
        else:
            landmark_label_list.append(0)
    landmark_object_XYsize = np.insert(landmark_object_XYsize,4,landmark_label_list,axis=1)
    nb_grid_landmarks = int(sum(landmark_object_XYsize[:,4]))
    if verbose >= 1:
        print(f'{nb_grid_landmarks} landmarks grid-certified')
    if verbose == 2:
        plt.figure(figsize=(10,5))
        plt.subplot(1,2,1)
        plt.plot(projected_hist)
        plt.subplot(1,2,2)
        sns.scatterplot(x=landmark_object_XYsize[:,1],y=landmark_object_XYsize[:,2], hue=landmark_object_XYsize[:,4])
        plt.plot(0,0,'ro')
        chart_scale=5000
        plt.xlim(-chart_scale,chart_scale)
        plt.ylim(-chart_scale,chart_scale)
        plt.show();

    # certifying lanmarks (2)
    # for each line of landmarks, validate any 2 objects where distance is equal to expected_distance
    # NB the vine grid is (expected_distance, expected_width)
    # run afer grid certification as landmark_object_list[4] is expected to exist in this code
    nb_of_lines = int(max(landmark_list[:,1])-min(landmark_list[:,1])+1) # (landmark_list[,1] = row number)
    if verbose ==1:
        print(f'analysing {nb_of_lines} rows of vines')
    angle_rad = best_angle *2*np.pi/360
    projected_hist = np.zeros((expected_distance,nb_of_lines)) # projection on vine line, group modulo expected_distance
    certified_count = np.zeros(nb_of_lines) # to count nb of certified landmarks for each line
    for object_nb in range(len(landmark_object_XYsize)):
        object_line = int(landmark_list[object_nb][1]-min(landmark_list[:,1]))
        projection = landmark_object_XYsize[object_nb][1]*cos(angle_rad)+landmark_object_XYsize[object_nb][2]*sin(angle_rad)
        # group by bins of bin_size, modulo expected_distance
        projection = int(np.round(projection/10/bin_size, decimals=0)*bin_size)
        projected_hist[int(projection % expected_distance)][object_line] += 1
    for object_nb in range(len(landmark_object_XYsize)):
        object_line = int(landmark_list[object_nb][1]-min(landmark_list[:,1]))
        projection = landmark_object_XYsize[object_nb][1]*cos(angle_rad)+landmark_object_XYsize[object_nb][2]*sin(angle_rad)
        projection = int(np.round(projection/10/bin_size, decimals=0)*bin_size)
        if projected_hist[int(projection % expected_distance)][object_line]>2: # nb of objects found to get certification
            landmark_object_XYsize[object_nb][4] += 1
            certified_count[object_line] += 1
    nb_line_landmarks = int(sum(landmark_object_XYsize[:,4]) - nb_grid_landmarks)
    if verbose >= 1:
        print(f'{nb_line_landmarks} landmarks distance-certified')
    if verbose == 2:
        for line in range(nb_of_lines):
            print(f'line {int(min(landmark_list[:,1])+line)}: {int(certified_count[line])}/{int(sum(projected_hist[:,line]))}')
        plt.figure()
        for line in range(nb_of_lines):
            plt.subplot(nb_of_lines,1,line+1)
            plt.plot(projected_hist[:,line])
        plt.show()
    landmark_object_XYsize = np.asarray(landmark_object_XYsize)

    return landmark_object_XYsize

def grid_align(landmark_object_XYsize, best_angle, distance_to_lidar, expected_width):
    """ returns a landmark array (nb, x, y size, certification_grade) aligned with vines
    rotate -90 + best_angle
    move sideways distance_to_lidar
    """
    angle_rad = (-90 + best_angle) * 2*np.pi/360
    landmarks = []
    for nb in range(len(landmark_object_XYsize)):
        X = landmark_object_XYsize[nb][1]*cos(angle_rad) + landmark_object_XYsize[nb][2]*sin(angle_rad)
        Y = -landmark_object_XYsize[nb][1]*sin(angle_rad) + landmark_object_XYsize[nb][2]*cos(angle_rad)
        X += (expected_width/2-distance_to_lidar)*10 # (back to mm)
        size = landmark_object_XYsize[nb][3]
        rank = landmark_object_XYsize[nb][4]
        landmarks.append([nb,X,Y,size,rank])
    landmarks = np.asarray(landmarks)
    return landmarks

#
#
# HERE IS THE CODE
#
"""
file_nb = 0
path_to_output_objects_file=f'data/outputObjectsFile{file_nb}.csv'
landmarks, best_angle, distance_to_lidar = process_lidar_file_to_landmarks(f'data/outputObjectsFile{file_nb}.csv',
                                                                           lidar_kwargs,
                                                                           verbose=2)
print("best angle ",best_angle, "distance to lidar ", distance_to_lidar)
"""

# End of certifying lanmark functions
# ---------------------------------------------------------------------------------------
# Beginning of vine map creation/update

# function to create an 'empty' vine_map csv file
# the file will have objects evenly distributed on a (expected_width, expected_distance) grid (in mm)
# rows on each side of 0, vines from 0 to nb_vines x expected_distance
# all points are graded default_grade=0.5 by default
# vine_map structure : obj_nb, x, y, size, grade
def create_new_vine_map(name=f'Log/vine_map_{plot_name}.csv',
                        expected_width=2000,
                        expected_distance=800,
                        nb_rows=4,
                        nb_vines=10,
                        default_size = 20, # default object size (mm)
                        default_grade=0.3, # default object grade
                        verbose=0):
    """
    create a new vine_map with expected objects on grid (expected_width, expected_distance) graded default_grade
    size nb_rows, nb_vines
    """
    vine_map = []
    obj_nb = 0
    for row_nb in range(nb_rows):
        for vine_nb in range(nb_vines):
            x = (row_nb - int(nb_rows/2)) * expected_width + expected_width/2
            y = vine_nb * expected_distance
            vine_map.append([obj_nb, x, y, default_size, default_grade])
            obj_nb +=1
    vine_map = np.asarray(vine_map)
    np.savetxt(name, vine_map, delimiter=',')
    if verbose >= 1:
        print(f'map with {obj_nb} objects on {expected_width} x {expected_distance} grid created, object size= {default_size}, object grade= {default_grade}')

# load vine_map from file or create a new one
def get_vine_map(path_to_vine_map_file,
                 create_new=False,
                 expected_width=2000, # this and the following parameters are only used if a new vine_map is created
                 expected_distance=800,
                 nb_rows=4,
                 nb_vines=10,
                 default_size = 20,
                 default_grade=0.3,
                 verbose=0):
    """ load a vine map or create new one
    this function returns a vine_map of structure (obj_nb, x, y, obj_size, obj_grade)"""
    if create_new == True:
        create_new_vine_map(name=path_to_vine_map_file, expected_width=expected_width,
                 expected_distance=expected_distance, nb_rows=nb_rows, nb_vines=nb_vines,
                 default_size=default_size, default_grade=default_grade)
    vine_map = np.loadtxt(path_to_vine_map_file, delimiter=",", dtype=float) # obj_nb, x, y, size, grade
    vine_map = np.asarray(vine_map)
    # draw map
    if verbose >= 1:
        print(f'map containing {len(vine_map)} objects loaded')
    if verbose == 2:
        plt.figure(figsize=(10,10))
        sns.scatterplot(x=vine_map[:,1],y=vine_map[:,2],hue=vine_map[:,4],size=vine_map[:,4])
        plt.xlim(min(vine_map[:,1])-200,max(vine_map[:,1])+200)
        plt.ylim(min(vine_map[:,2])-200,max(vine_map[:,2])+200)
        plt.grid()
        plt.title(f'vine_map from {path_to_vine_map_file}')
        plt.show();
    return vine_map

def position_and_map_update(expected_X,
                            expected_Y,
                            path_to_vine_map_file,
                            create_new_map=False,
                            update_map=False,
                            landmarks=None,
                            best_angle=0,
                            distance_to_lidar=0,
                            bin_size=10,
                            expected_width=200,
                            crop_distance=10000,
                            verbose=0):

    # create landmarks_real of best-certified landmarks:
    # landmarks table of expected x, expected y coordinates, for landmarks of highest or two highest grades
    # original landmark table is relative to lidar, landmark_real is absolute to match vine_map
    grade = max(landmarks[:,4])
    # try with highest grade only
    landmarks_real = [[row[1]+expected_X, row[2]+expected_Y] for row in landmarks if row[4]>=grade]
    if len(landmarks_real)<7: # if not enough points, get two highest grades
        landmarks_real = [[row[1]+expected_X, row[2]+expected_Y] for row in landmarks if row[4]>=grade-1]
    if verbose >= 1:
        print(f'selected {len(landmarks_real)} landmarks of highest grade out of {len(landmarks)} items')

    # get vine_map
    vine_map = get_vine_map(path_to_vine_map_file, create_new=create_new_map, verbose=verbose)

    # select local points
    # crop_distance = 10000 mm by default, to build a smaller vine_map around the expected lidar position
    X_min = expected_X - crop_distance
    X_max = expected_X + crop_distance
    Y_min = expected_Y - crop_distance
    Y_max = expected_Y + crop_distance

    # build local vine map (vine_map_small)
    vine_map_small = [[row[1], row[2]] for row in vine_map if row[1]>=X_min and row[1]<=X_max and row[2]>=Y_min and row[2]<=Y_max]
    nbrs = NearestNeighbors(n_neighbors=1, algorithm='ball_tree').fit(vine_map_small)
    if verbose >= 1:
        print(f'current local vine_map size is {len(vine_map_small)} items')

    # calculate corrections to position (position error as cor_X (mm), cor_Y (mm))
    count_distances = 0 # counter of objects where distances < bin_size/2
    #(in such a case, the object is considered perfectly matched within vine_map)
    sum_distances = [0] # sum of distances to nearest vine_map object
    best_cor_Y = 0
    best_cor_X = 0
    for Y_index_nb in range(100): # loop through -50 to +50 cm for Y (this assumes expected_Y truly falls within this range)
        cor_Y = (Y_index_nb-50)*10
        for X_index_nb in range(10): # loop within bin_size as grid_align has centered X
            cor_X = (X_index_nb-5)*10
            temp_landmarks = [[row[0]+cor_X, row[1]+cor_Y] for row in landmarks_real]
            distances, indices = nbrs.kneighbors(temp_landmarks)
            if sum(distances[:,0]<bin_size/2*10)>count_distances:
                count_distances = sum(distances[:,0]<bin_size/2*10) # convert bin_size to mm (hence the *10)
                sum_distances = sum(distances)
                best_cor_X = cor_X
                best_cor_Y = cor_Y

    X_position = expected_X + best_cor_X + (-expected_width/2 + distance_to_lidar)*10
    Y_position = expected_Y + best_cor_Y
    direction = best_angle - 180

    if verbose >= 1:
        print(f'matched {count_distances} objects out of {len(landmarks_real)} within {round(bin_size/2*10)} mm, sum of distances= {round(sum_distances[0])} mm, best correction = ({best_cor_X}, {best_cor_Y}) mm')
        print(f'true position is X= {X_position}, Y= {Y_position}, direction of {direction}° !!! (check this direction data) !!!')
        print()

    # results of matching for each certified landmark (map item nb, distance and x and y split of this distance)
    if verbose == 2:
        print('results of vine_map matching for each certified landmark')
        print('map item nb, distance and x and y split of this distance:')
        temp_landmarks = [[row[0]+best_cor_X, row[1]+best_cor_Y] for row in landmarks_real]
        distances, indices = nbrs.kneighbors(temp_landmarks)
        for landmark in range(len(temp_landmarks)):
            vine_nb = int(indices[landmark])
            X_vector = round(vine_map_small[vine_nb][0] - temp_landmarks[landmark][0])
            Y_vector = round(vine_map_small[vine_nb][1] - temp_landmarks[landmark][1])
            print(f'map item nb {vine_nb}, distance {round(distances[landmark][0])} mm as x, y: {X_vector}, {Y_vector}')
        print()

    # plot vine_map and landmarks around lidar
    if verbose == 2:
        temp_landmarks = [[row[0]+best_cor_X, row[1]+best_cor_Y] for row in landmarks_real]
        all_landmarks_real = [[row[1]+expected_X+best_cor_X, row[2]+expected_Y+best_cor_Y, row[3], row[4]] for row in landmarks]
        plt.figure(figsize=(15,15))
        vine_map_small = np.asarray(vine_map_small)
        temp_landmarks = np.asarray(temp_landmarks)
        all_landmarks_real = np.asarray(all_landmarks_real)
        plt.scatter(x=vine_map_small[:,0],y=vine_map_small[:,1], label="vine_map points")
        plt.scatter(x=all_landmarks_real[:,0],y=all_landmarks_real[:,1], label = "landmarks")
        plt.scatter(x=temp_landmarks[:,0],y=temp_landmarks[:,1], label="certified landmarks")
        plt.plot(X_position, Y_position, 'ro', label="lidar position")
        chart_scale = (Y_max - Y_min)/4
        plt.xlim(expected_X+best_cor_X-chart_scale,expected_X+best_cor_X+chart_scale)
        plt.ylim(expected_Y+best_cor_Y-chart_scale,expected_Y+best_cor_Y+chart_scale)
        plt.legend()
        plt.grid()
        plt.show();

    if update_map :
        # update vine_map (place new points, recalculate existing points positions, delete duplicates and recalculate all grades)
        nbrs = NearestNeighbors(n_neighbors=1, algorithm='ball_tree').fit(vine_map[:,1:3])

        # stats
        total_index = 0
        group_index = 0
        new_index = 0
        deleted_index = 0
        # params
        distance_for_downgrading = 4000 # (mm)
        down_grade = 0.2

        for row in landmarks:
            X = row[1]+expected_X+best_cor_X
            Y = row[2]+expected_Y+best_cor_Y
            distance, indice = nbrs.kneighbors([[X,Y]])
            distance = distance[0][0]
            indice = indice[0][0]

            if distance<bin_size*10: # convert bin_size in mm
                vine_map[indice][1] = vine_map[indice][1]*.9 +X*.1
                vine_map[indice][2] = vine_map[indice][2]*.9 +Y*.1
                vine_map[indice][3] = vine_map[indice][3]*.9 +row[3]*.1
                vine_map[indice][4] += 0.5 + row[4]/2 # certif_grade=0 -> add 0.5, =1 -> add 1, =2 -> add 1.5
                group_index += 1
            else:
                vine_map = np.concatenate((vine_map, [[len(vine_map), X, Y, row[3], 0.3 + row[4]/4]]), axis=0)
                new_index += 1

        total_index = len(vine_map)
        for row in vine_map: # fade out effect : downgrade all objects within distance_for_downgrading
            X = expected_X+best_cor_X
            Y = expected_Y+best_cor_Y
            if sqrt((row[1]-X)**2+(row[2]-Y)**2) < distance_for_downgrading:
                row[4] -= down_grade
        vine_map = [row for row in vine_map if row[4]>0] # delete objects with grade <=0
        vine_map = np.asarray(vine_map)
        deleted_index = total_index - len(vine_map)
        if verbose >= 1:
            print(f'{group_index} points grouped, {new_index} points added, {deleted_index} points deleted, map size {len(vine_map)} points')

        # delete duplicates
        # set obj_nb to -1 if 2nd duplicate (ie for duplicate with highest obj_nb), then delete items with obj_nb<0
        nbrs = NearestNeighbors(n_neighbors=2, algorithm='ball_tree').fit(vine_map[:,1:3])
        duplicate_index = 0
        for row in vine_map:
            X = row[1]
            Y = row[2]
            distance, indice = nbrs.kneighbors([[X,Y]])
            distance = distance[0][1]
            indice = int(indice[0][1])
            if distance<bin_size*10: # add objects size elements ? eg distance - size1 - size2 < bin_size/3*10 ?
                if row[0]>vine_map[indice][0]:
                    row[0] = -1
                    duplicate_index +=1
        vine_map = [row for row in vine_map if row[0]>=0]
        vine_map = np.asarray(vine_map)
        if verbose >= 1:
            print(f'{duplicate_index} duplicate points deleted, map size reduced to {len(vine_map)}')

        np.savetxt(path_to_vine_map_file, vine_map, delimiter=',')
        if verbose >= 1:
            print(f'map saved under {path_to_vine_map_file}')

    return X_position, Y_position, direction

#
#
# HERE IS THE CODE
#

if __name__ == "__main__":
    X_position = 0
    Y_position = 0

    for file_nb in range(1,10):

        print()
        print(f'processing file nb {file_nb}')

        # load object csv file and process landmark calculations
    #    file_nb = 7
        path_to_output_objects_file=f'Log/outputObjectsFile{file_nb}.csv'
        landmarks, best_angle, distance_to_lidar = process_lidar_file_to_landmarks(f'Log/outputObjectsFile{file_nb}.csv',
                                                                                lidar_kwargs,
                                                                                verbose=1)

        # expected lidar position (estimation)
        expected_X = 0 #X_position # (mm)
        expected_Y = Y_position + 900 # (mm)
        # other parmeters
        update_map = True # update vine_map file after process
        bin_size = lidar_kwargs['bin_size']
        expected_width = lidar_kwargs['expected_width']
        # vine_map file name and path, update flag
        # plot_name = 'AH222' (this line has been moved up)
        path_to_vine_map_file = f'Log/vine_map_{plot_name}.csv'
        if file_nb == 0:
            create_new_map = True
        else:
            create_new_map = False

        # calculation true position and update vine_map
        X_position, Y_position, direction = position_and_map_update(expected_X,
                                    expected_Y,
                                    path_to_vine_map_file,
                                    create_new_map=create_new_map,
                                    update_map=update_map,
                                    landmarks=landmarks,
                                    best_angle=best_angle,
                                    distance_to_lidar=distance_to_lidar,
                                    bin_size=bin_size,
                                    expected_width=expected_width,
                                    crop_distance=10000,
                                    verbose=1)

        print(f'file_nb {file_nb} done, position= {X_position}, {Y_position}, direction = {direction}')

    print("")
    print("showing map")
    # plot full vine_map
    plt.figure(figsize=(15,15))
    # plot_name = 'AH222'
    path_to_vine_map_file = f'Log/vine_map_{plot_name}.csv'
    vine_map = get_vine_map(path_to_vine_map_file, create_new=False, verbose=1)
    vine_map = np.asarray(vine_map)
    sns.scatterplot(x=vine_map[:,1],y=vine_map[:,2],size=vine_map[:,4], hue=vine_map[:,4])
    plt.plot(X_position, Y_position, 'ro')
    plt.xlim(min(vine_map[:,1])-200,max(vine_map[:,1])+200)
    plt.ylim(min(vine_map[:,2])-200,max(vine_map[:,2])+200)
    plt.grid()
    plt.show();
