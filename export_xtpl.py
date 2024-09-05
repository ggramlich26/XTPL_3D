def export_xtpl_code(points: list, function_name, filepath):
    """creates a text document with the xtpl code"""

    def get_maximum_z_level(point_list: list):
        """returns the maximus z-value of the plot in mm"""  # Not used right now
        max_z = 0
        for polylines in point_list:
            for coordinates in polylines:
                if coordinates[2] > max_z:
                    max_z = coordinates[2]
        return max_z

    def check_y_direction(points: list):
        """checks if the y-axis movement is only in negative direction and if not, flips the order of coordinates in the points list (for each polyline individually)"""
        for k, polyline in enumerate(points):
            for l, coordinates in enumerate(polyline):
                if coordinates[1] < coordinates[l + 1]:
                    continue
                else:
                    print('hab nochmal was geändert')
                    # points[k] = polyline[::-1]

    # check_y_direction(points)
    def check_order(lst: list) -> None:
        def take_second(elem):
            return elem[1]

        for k, polylines in enumerate(lst):
            if lst == sorted(lst, key=take_second):
                print('step', k, 'sorted')
            else:
                print('step', k, 'not sorted')

    #check_order(points)

    def delete_name_function():
        """deletes the existing name function in the txt file. This function can be deleted later and is not needed for the final program"""
        with open(r'C:\Users\ubjxf\Documents\Bachelorarbeit\XTPL\Documents\test_text.txt', 'r') as f:
            lines = f.readlines()

        with open(r'C:\Users\ubjxf\Documents\Bachelorarbeit\XTPL\Documents\test_text.txt', 'w') as f:
            deleting = False
            for line in lines:
                if 'begin name' in line:
                    deleting = True
                elif not deleting:
                    f.write(line)
                elif 'end' in line:
                    deleting = False

    #delete_name_function()

    # function_name = 'name'
    #print(filepath)



    with open(filepath, 'w') as xtpl_file:

        xtpl_file.write('#XTPL language 1.2\n')
        xtpl_file.write('/* This is auto-generated file by automatic conversions from dxf file\n\n'
                        'DO NOT EDIT this file. Any changes will be lost when conversion is run again!\n'
                        'File generated with sorting: 2, with scale: 1.0000 */ \n\n')
        xtpl_file.write('set before_called _false_\n')
        xtpl_file.write('set before_ticks 0\n')
        xtpl_file.write('// variables to restore prev velocity parameters.')
        xtpl_file.write(
            '// variables to restore prev velocity parameters. \nset prev_vel_x 1\nset prev_vel_y 1\nset prev_vel_z 1\nset prev_acc_x 1\nset prev_acc_y 1\nset prev_acc_z 1\n\nset prev_dec_x 1\nset prev_dec_y 1\nset prev_dec_z 1\n')
        xtpl_file.write(
            '// variables to restore essential positions.\nset prev_dep_area_x ""\nset prev_dep_area_y ""\nset prev_dep_area_z ""\nset global_starting_point ""\n')
        # before
        xtpl_file.write("""
begin before
    make $prev_vel_x = getvel (axis:x)
    make $prev_vel_y = getvel (axis:y)
    make $prev_vel_z = getvel (axis:z)

    make $prev_acc_x = getacc (axis:x)
    make $prev_acc_y = getacc (axis:y)
    make $prev_acc_z = getacc (axis:z)

    make $prev_dec_x = getdec (axis:x)
    make $prev_dec_y = getdec (axis:y)
    make $prev_dec_z = getdec (axis:z)

    if pexists(name:dep_area) make $prev_dep_area_x = getpoint(name:"dep_area" axis:x)
    if pexists(name:dep_area) make $prev_dep_area_y = getpoint(name:"dep_area" axis:y)
    if pexists(name:dep_area) make $prev_dep_area_z = getpoint(name:"dep_area" axis:z)
    make $global_starting_point = getpos()

    make $before_called = _true_
    user_before
    make $before_ticks = $__ticks__
end\n""")

        # after
        xtpl_file.write("""
begin after
    setvel axis:x vel:$prev_vel_x
    setvel axis:y vel:$prev_vel_y
    setvel axis:z vel:$prev_vel_z
    
    setacc axis:x acc:$prev_acc_x
    setacc axis:y acc:$prev_acc_y
    setacc axis:z acc:$prev_acc_z

    setdec axis:x dec:$prev_dec_x
    setdec axis:y dec:$prev_dec_y
    setdec axis:z dec:$prev_dec_z

    if pexists(name:dep_area) psave name:dep_area x:$prev_dep_area_x y:$prev_dep_area_y z:$prev_dep_area_z
    if $__render_mode__ vecmoveto point:$global_starting_point wait:_true_
    user_after
    echo "Project execution time taken: " + time($__ticks__ - $before_ticks)
end\n""")

        # on stop
        xtpl_file.write("""
begin _on_stop_
   press 0
   stop_motors
   if ($before_called) after // restores velocities used before script run
end\n""")

        # getRotatedX
        xtpl_file.write("""
begin GetRotatedX x y angle
    set fi = $angle * $__pi__ / 180.0
    return ($x * cos($fi) - $y * sin($fi))
end\n""")

        # getRotatedY
        xtpl_file.write("""
begin GetRotatedY x y angle
    set fi = $angle * $__pi__ / 180.0
    return ($x * sin($fi) + $y * cos($fi))
end\n\n""")

        # begin the function with the given function name
        xtpl_file.write(str('begin ' + function_name + '\n'))
        # call the before function
        xtpl_file.write('    before\n')
        # add the progress
        xtpl_file.write('    const progr_part ' + str(len(points)) + '\n')
        xtpl_file.write('    const progr_start 0' + '\n')
        xtpl_file.write('    const progr_total ' + str(len(points)) + '\n')
        # save the start position of the printer
        xtpl_file.write('    set start_x = getpos (axis:x)\n')
        xtpl_file.write('    set start_y = getpos (axis:y)\n')
        xtpl_file.write('    set start_z = getpos (axis:z)\n')

        xtpl_file.write(
            '    set rez_done_in_middle = _false_  //this variable will be set to _true_ if going to reservoir was perfored in a middle of the polyline\n')
        # go to the start position of the print
        xtpl_file.write('    go_to_medium_high_position point:{$start_x +(' + str(
            format(points[0][0][0], '.10f')) + '), $start_y+(' + str(
            format(points[0][0][1], '.10f')) + '), $start_z +(' + str(
            format(points[0][0][2], '.10f')) + ')} start_z:$start_z\n')
        xtpl_file.write('    //if _not_ starting_in_contact() go_down z_level:0\n')

        for k, polylines in enumerate(points):              #iterates through  all the points to create a path
            for i, coordinates in enumerate(polylines):
                if i <= (len(polylines) - 2):
                    next_coordinates = polylines[i + 1]

                    #define from_x from_y and from_z
                    from_x = str('(' + format(coordinates[0], '.10f') + ')')
                    from_y = str('(' + format(coordinates[1], '.10f') + ')')
                    from_z = str('(' + format(coordinates[2], '.10f') + ')')

                    #define step_x step_y and step_z
                    step_x = str(format(next_coordinates[0] - coordinates[0], '.10f'))
                    step_y = str(format(next_coordinates[1] - coordinates[1], '.10f'))
                    step_z = str(format(next_coordinates[2] - coordinates[2], '.10f'))


                    #write teh commands to the new file
                    #if the line is the first in the polyline, the parameter is_first needs to be set _true_
                    if i == 0:
                        xtpl_file.write(
                            str('    draw_line_3d from_x:$start_x +' + from_x + ' from_y:$start_y +' + from_y + ' from_z:$start_z +' + from_z + ' step_x:' + step_x + ' step_y:' + step_y + ' step_z:' + step_z + ' is_first:_true_ is_last:_false_ layer:0\n'))

                    # if the line is the last in the polyline, the parameter is_last needs to be set _true_
                    elif i == (len(polylines) - 2):
                        xtpl_file.write(
                            str('    draw_line_3d from_x:$start_x +' + from_x + ' from_y:$start_y +' + from_y + ' from_z:$start_z +' + from_z + ' step_x:' + step_x + ' step_y:' + step_y + ' step_z:' + step_z + ' is_first:_false_ is_last: _true_ layer:0\n'))
                        break

                    #all other lines can be added with is_first and is_last beeing set  to _false_
                    elif i < (len(polylines) - 2):
                        draw_line_3d_command = str(
                            '    draw_line_3d from_x:$start_x +' + from_x + ' from_y:$start_y +' + from_y + ' from_z:$start_z +' + from_z + ' step_x:' + step_x + ' step_y:' + step_y + ' step_z:' + step_z + ' is_first:_false_ is_last:_false_ layer:0\n')
                        xtpl_file.write(draw_line_3d_command)


            #add movement to go up after the last polyline and update the progress
            if k == len(points) - 1:
                xtpl_file.write('    go_up\n')
                xtpl_file.write('    progress step:$progr_total of:$progr_total\n')
                xtpl_file.write('    after\n')
                xtpl_file.write('end')
                return

            #update the progress after each polyline and check add chek_goto_rez
            xtpl_file.write(
                '    progress step: ' + str((k + 1) / len(points)) + ' * $progr_part + $progr_start of: $progr_total\n')
            xtpl_file.write('    echo msg: "Printed Polyline ' + str(k+1) + ' of ' + str(len(points)) + '"\n')
            xtpl_file.write('    check_goto_rez\n')
            #move to the next polyline
            xtpl_file.write('    go_to_medium_high_position point:{$start_x +(' + str(
                format(points[k + 1][0][0], '.10f')) + '), $start_y+(' + str(
                format(points[k + 1][0][1], '.10f') + '), $start_z +(' + str(
                format(points[k + 1][0][2], '.10f')) + ')} start_z:$start_z\n'))
            # xtpl_file.write(str('    go_to_position x:$start_x +' + str(points[k + 1][0][0]) + ' y:$start_y +' + str(points[k + 1][0][1]) + '\n'))
            # xtpl_file.write('    go_down z_level:0\n')


"""
        for i in range(len(points)):
            for j in range(len(points[i]) -1 ):
                '''from_x = str('(' + format(points[i][j][0], '.10f') + '-$start_x' + ')')
                from_y = str('(' + format(points[i][j][1], '.10f') + '-$start_y' + ')')
                from_z = str('(' + format(points[i][j][2], '.10f') + '-$start_z' + ')')

                step_x = str(format(points[i][j + 1][0] - points[i][j][0], '.10f'))
                step_y = str(format(points[i][j + 1][1] - points[i][j][1], '.10f'))
                step_z = str(format(points[i][j + 1][2] - points[i][j][2], '.10f'))
                step_z_last = str(format(points[i][j + 1][2], '.10f'))'''
                from_x = str('(' + format(points[i][j][0], '.10f') + ')')
                from_y = str('(' + format(points[i][j][1], '.10f') + ')')
                from_z = str('(' + format(points[i][j][2], '.10f') + ')')

                step_x = str(format(points[i][j + 1][0] - points[i][j][0], '.10f'))
                step_y = str(format(points[i][j + 1][1] - points[i][j][1], '.10f'))
                step_z = str(format(points[i][j + 1][2] - points[i][j][2], '.10f'))
                step_z_last = str(format(points[i][j + 1][2], '.10f'))

                if j == 0:
                    xtpl_file.write(str('    draw_line_3d from_x:' + from_x + ' from_y:' + from_y + ' from_z:' + from_z + ' step_x:' + step_x + ' step_y:' + step_y + ' step_z:' + step_z + ' is_first:_true_ is_last:_false_ layer:0\n'))

                elif j == (len(points[i]) - 1):
                    print('bin in elif drin')
                    xtpl_file.write(str('    draw_line_3d from_x:' + from_x + ' from_y:' + from_y + ' from_z:' + from_z + ' step_x:' + step_x + ' step_y:' + step_y + ' step_z: 0' + ' is_first:_false_ is_last:false layer:0\n'))

                else:
                    draw_line_3d_command = str('    draw_line_3d from_x:' + from_x + ' from_y:' + from_y + ' from_z:' + from_z + ' step_x:' + step_x + ' step_y:' + step_y + ' step_z:' + step_z + ' is_first:_false_ is_last:_false_ layer:0\n')
                    xtpl_file.write(draw_line_3d_command)

                # add progress here

            if i == len(points) - 1:
                xtpl_file.write('    go_up\n')
                xtpl_file.write('end')
                return

            xtpl_file.write('    go_up\n')
            xtpl_file.write(str('    go_to_position x:(' + str(points[i + 1][0][0]) + ') y:(' + str(points[i + 1][0][1]) + ')' + '\n'))
            xtpl_file.write('    go_down z_level:0\n')"""
