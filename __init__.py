# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DrawJoinFeature
                                 A QGIS plugin
 Dessiner l'entité jointe à partir d'une sélection
                             -------------------
        begin                : 2017-05-22
        copyright            : (C) 2017 by Hugo Roussaffa / Geodatup
        email                : contact@geodatup.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load DrawJoinFeature class from file DrawJoinFeature.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .Draw_Join_Feature import DrawJoinFeature
    return DrawJoinFeature(iface)
