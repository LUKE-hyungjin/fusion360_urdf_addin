# -*- coding: utf-8 -*-
"""
Created on Sun May 12 20:46:26 2019

@author: syuntoku
"""

import adsk, os
import re
from xml.etree.ElementTree import Element, SubElement
from . import Link, Joint, Material
from ..utils import utils

def write_link_urdf(joints_dict, repo, links_xyz_dict, file_name, inertial_dict):
    """
    Write links information into urdf "repo/file_name"


    Parameters
    ----------
    joints_dict: dict
        information of the each joint
    repo: str
        the name of the repository to save the xml file
    links_xyz_dict: vacant dict
        xyz information of the each link
    file_name: str
        urdf full path
    inertial_dict:
        information of the each inertial

    Note
    ----------
    In this function, links_xyz_dict is set for write_joint_tran_urdf.
    The origin of the coordinate of center_of_mass is the coordinate of the link
    """
    with open(file_name, mode='a') as f:

        # for base_link
        center_of_mass = inertial_dict['base_link']['center_of_mass']
        Material_name,color=Material.material('base_link')
        Material_name = re.sub(" ","",str(Material_name))
        link = Link.Link(name='base_link', xyz=[0,0,0],
            center_of_mass=center_of_mass, repo=repo,
            mass=inertial_dict['base_link']['mass'],
            inertia_tensor=inertial_dict['base_link']['inertia'],
            material_name = Material_name
            )
        links_xyz_dict[link.name] = link.xyz
        link.make_link_xml()
        f.write('  ')
        f.write(link.link_xml)
        f.write('\n')
        app = adsk.core.Application.get()
        product = app.activeProduct
        design  = adsk.fusion.Design.cast(product)
        root = design.rootComponent
        allOccs = root.occurrences
        appearance_dict = {}
        for occs in allOccs:
            appearance_dict[str(occs.component.name)] = str(occs.component.material.appearance.name)

        # others
        for joint in joints_dict:
            name = joints_dict[joint]['child']
            find_name = name[:-2]
            if find_name in appearance_dict.keys():
                appearance_name = appearance_dict.pop(name[:-2])
                appearance_name = re.sub(" ","",appearance_name)
            center_of_mass = \
            [ i-j for i, j in zip(inertial_dict[name]['center_of_mass'], joints_dict[joint]['xyz'])]
            link = Link.Link(name=name, xyz=joints_dict[joint]['xyz'],\
                center_of_mass=center_of_mass,\
                repo=repo, mass=inertial_dict[name]['mass'],\
                inertia_tensor=inertial_dict[name]['inertia'],
                material_name=appearance_name)
            links_xyz_dict[link.name] = link.xyz
            link.make_link_xml()
            f.write('  ')
            f.write(link.link_xml)
            f.write('\n')


def write_joint_urdf(joints_dict, repo, links_xyz_dict, file_name):
    """
    Write joints and transmission information into urdf "repo/file_name"


    Parameters
    ----------
    joints_dict: dict
        information of the each joint
    repo: str
        the name of the repository to save the xml file
    links_xyz_dict: dict
        xyz information of the each link
    file_name: str
        urdf full path
    """

    with open(file_name, mode='a') as f:
        for j in joints_dict:
            parent = joints_dict[j]['parent']
            child = joints_dict[j]['child']
            joint_type = joints_dict[j]['type']
            upper_limit = joints_dict[j]['upper_limit']
            lower_limit = joints_dict[j]['lower_limit']
            try:
                xyz = [round(p-c, 6) for p, c in \
                    zip(links_xyz_dict[parent], links_xyz_dict[child])]  # xyz = parent - child
            except KeyError as ke:
                app = adsk.core.Application.get()
                ui = app.userInterface
                ui.messageBox("There seems to be an error with the connection between\n\n%s\nand\n%s\n\nCheck \
whether the connections\nparent=component2=%s\nchild=component1=%s\nare correct or if you need \
to swap component1<=>component2"
                % (parent, child, parent, child), "Error!")
                quit()

            joint = Joint.Joint(name=j, joint_type = joint_type, xyz=xyz, \
            axis=joints_dict[j]['axis'], parent=parent, child=child, \
            upper_limit=upper_limit, lower_limit=lower_limit)
            joint.make_joint_xml()
            joint.make_transmission_xml()
            f.write('  ')
            f.write(joint.joint_xml)
            f.write('\n')

def write_urdf(joints_dict, links_xyz_dict, inertial_dict, package_name, robot_name, save_dir):
    try: os.mkdir(save_dir + '/urdf')
    except: pass

    file_name = save_dir + '/urdf/{}.xacro'.format(robot_name)  # the name of urdf file
    repo = package_name + '/meshes/'  # the repository of binary stl files
    write_link_urdf(joints_dict, repo, links_xyz_dict, file_name, inertial_dict)
    write_joint_urdf(joints_dict, repo, links_xyz_dict, file_name)
    with open(file_name, mode='a') as f:
        f.write('</robot>\n')

def write_materials_xacro(joints_dict, links_xyz_dict, inertial_dict, package_name, robot_name, save_dir):
    try: os.mkdir(save_dir + '/urdf')
    except: pass

    file_name = save_dir + '/urdf/{}.material'.format(robot_name)  # the name of urdf file
    with open(file_name, mode='a') as f:
        f.write('<?xml version="1.0" ?>\n')
        f.write('<robot name="{}">\n'.format(robot_name))
        app = adsk.core.Application.get()
        product = app.activeProduct
        design  = adsk.fusion.Design.cast(product)
        root = design.rootComponent
        allOccs = root.occurrences
        result = []
        for occs in allOccs:
            com_name = occs.component.name
            material_name, color = Material.material(com_name)
            if str(material_name) not in result:
                result.append(str(material_name))
                material_name = re.sub(" ","",material_name)
                f.write('  <material name="{}">\n'.format(material_name))
                f.write('    <color rgba="{}"/>\n'.format(color))
                f.write('  </material>\n')
        f.write('\n')

def write_transmissions_xacro(joints_dict, links_xyz_dict, inertial_dict, package_name, robot_name, save_dir):
    """
    Write joints and transmission information into urdf "repo/file_name"


    Parameters
    ----------
    joints_dict: dict
        information of the each joint
    repo: str
        the name of the repository to save the xml file
    links_xyz_dict: dict
        xyz information of the each link
    file_name: str
        urdf full path
    """

    file_name = save_dir + '/urdf/{}.tran'.format(robot_name)  # the name of urdf file
    with open(file_name, mode='a') as f:
        for j in joints_dict:
            parent = joints_dict[j]['parent']
            child = joints_dict[j]['child']
            joint_type = joints_dict[j]['type']
            upper_limit = joints_dict[j]['upper_limit']
            lower_limit = joints_dict[j]['lower_limit']
            try:
                xyz = [round(p-c, 6) for p, c in \
                    zip(links_xyz_dict[parent], links_xyz_dict[child])]  # xyz = parent - child
            except KeyError as ke:
                app = adsk.core.Application.get()
                ui = app.userInterface
                ui.messageBox("There seems to be an error with the connection between\n\n%s\nand\n%s\n\nCheck \
whether the connections\nparent=component2=%s\nchild=component1=%s\nare correct or if you need \
to swap component1<=>component2"
                % (parent, child, parent, child), "Error!")
                quit()

            joint = Joint.Joint(name=j, joint_type = joint_type, xyz=xyz, \
            axis=joints_dict[j]['axis'], parent=parent, child=child, \
            upper_limit=upper_limit, lower_limit=lower_limit)
            if joint_type != 'fixed':
                joint.make_transmission_xml()
                f.write('  ')
                f.write(joint.tran_xml)
                f.write('\n')


def add_file(robot_name, save_dir):
    file_name = save_dir + '/{}.urdf'.format(robot_name) 
    filenames = [ save_dir +f'/urdf/{robot_name}.material', save_dir +f'/urdf/{robot_name}.tran', save_dir +f'/urdf/{robot_name}.xacro']

    with open(file_name, mode ='w') as outfile:
        for filename in filenames:
            with open(filename) as file:
                outfile.write(file.read())
            os.remove(filename)
    os.rmdir(save_dir+'/urdf')
