# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DrawJoinFeature
                                 A QGIS plugin
 Dessiner l'entité jointe à partir d'une sélection
                              -------------------
        begin                : 2017-05-22
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Hugo Roussaffa / Geodatup
        email                : contact@geodatup.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt, QObject, SIGNAL
from PyQt4.QtGui import QAction, QIcon, QDialog, QFormLayout
from qgis.gui import (QgsFieldComboBox, QgsMapLayerComboBox,
                      QgsMapLayerProxyModel)
from qgis.core import QgsMessageLog, QgsFeatureRequest, QgsFeature, QgsVectorLayer, QgsMapLayerRegistry

# Initialize Qt resources from file resources.py
import resources

# Import the code for the DockWidget
from Draw_Join_Feature_dockwidget import DrawJoinFeatureDockWidget
import os.path


class DrawJoinFeature:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'DrawJoinFeature_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Dessiner_entite_jointe')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'DrawJoinFeature')
        self.toolbar.setObjectName(u'DrawJoinFeature')

        #print "** INITIALIZING DrawJoinFeature"

        self.pluginIsActive = False
        self.dockwidget = None



    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('DrawJoinFeature', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/DrawJoinFeature/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Dessiner_entite_jointe'),
            callback=self.run,
            parent=self.iface.mainWindow())

    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""
        #on clean les combobox
        self.dockwidget.list_exu.clear()
        self.dockwidget.list_bv.clear()

        #print "** CLOSING DrawJoinFeature"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None


        self.pluginIsActive = False


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        #print "** UNLOAD DrawJoinFeature"


        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Dessiner_entite_jointe'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    #--------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        if not self.pluginIsActive:
            self.pluginIsActive = True

            #print "** STARTING DrawJoinFeature"

            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget == None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = DrawJoinFeatureDockWidget()
                
                # connecter le bouton à l'action sur la fonction drawEntity
                self.dockwidget.DrawButton.clicked.connect(self.drawEntity)

                
            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            

            self.dockwidget.show()

        # HACk : on clean les combobox même lorsqu'on clique plusieurs fois sur le bouton du plugin
        self.dockwidget.list_exu.clear()
        self.dockwidget.list_bv.clear()

        ## Evo : faire un menu dynamique connecté aux modifications faites sur le menu Layers

        self.layersListUp2Date()

        # on créer 2 connections aux evenements add/remove layer dans le legendLayer pannel
        QgsMapLayerRegistry.instance().legendLayersAdded.connect(self.layersListUp2Date)
        QgsMapLayerRegistry.instance().layersRemoved.connect(self.layersListUp2Date)


        # on créer une connection aux evenements de changement d'index des combobox
        QObject.connect(self.dockwidget.list_exu,SIGNAL("currentIndexChanged(int)"),self.layerChanged)
        QObject.connect(self.dockwidget.list_bv,SIGNAL("currentIndexChanged(int)"),self.layerChanged)

        # On catch l'index de la sélection de la combo
       # exuLyrIdx = self.dockwidget.list_exu.currentIndex()
       # bvLyrIdx = self.dockwidget.list_bv.currentIndex()

        
        # on active le bouton de selection d'entité
        self.iface.actionSelect().trigger()

        # on connect le layer sélectionné dans la combobox avec l'evenement de sélection d'entité sur la carte (afin d'avoir toujours
        # les info mises à jour dans l'interface)
       # self.selectionConnectByLayerIdx(exuLyrIdx)




    def saveCurrentLayersId(self, dockwidget): 
        '''
            permet de sauvegarder le choix des layers si une couche est ajoutée ou supprimée
            On transmet à la fonction le widget de la combobox
        '''
        identifier = dockwidget.itemData(dockwidget.currentIndex())
        #QgsMessageLog.logMessage("identifier   " + str(identifier), "Dessiner_entite_jointe")
        
        return identifier

    def layerChanged(self):

        registry = QgsMapLayerRegistry.instance()
        identifier_exu = self.dockwidget.list_exu.itemData(self.dockwidget.list_exu.currentIndex())
        identifier_bv = self.dockwidget.list_bv.itemData(self.dockwidget.list_bv.currentIndex())
        self.exuLyr = registry.mapLayer(identifier_exu)
        self.bvLyr = registry.mapLayer(identifier_bv)

        QgsMessageLog.logMessage("identifier_exu : " + str(identifier_exu) + " self.exuLyr : " + str(self.exuLyr), "Dessiner_entite_jointe")

        #Et IMPORTANT on reconnect le layer sélectionné dans la combobox avec l'evenement de sélection d'entité sur la carte (afin d'avoir toujours
        # les info mises à jour dans l'interface)
        self.selectionConnectByLayerIdx(self.exuLyr)
        #rendre la couche exutoire active
        self.iface.setActiveLayer(self.exuLyr)


    def layersListUp2Date(self): 

        # on test que la liste est bien populée        
        if self.dockwidget.list_exu.count() != 0:
             # il faut garder en mémoire les layers définis dans les combobox
            exulyrId = self.saveCurrentLayersId(self.dockwidget.list_exu)
            bvlyrId = self.saveCurrentLayersId(self.dockwidget.list_bv)           

            # Puis on poutre la liste
            self.dockwidget.list_exu.clear()
            self.dockwidget.list_bv.clear()


        #for layer in sorted(QgsMapLayerRegistry.instance().mapLayers().values()):
        for layer in self.iface.legendInterface().layers():
            QgsMessageLog.logMessage("layer name loaded :  "  + str(layer.name()), "Dessiner_entite_jointe")
            
            # on popule les combobox
            self.dockwidget.list_exu.addItem(layer.name(), layer.id())
            self.dockwidget.list_bv.addItem(layer.name(), layer.id())

        # réAffectation des index des combo après une modification de la liste des couches
        
        try : # d'abord Exutoire. On test que l'identifiant est définit
            exulyrId 
        except NameError:
            # On défini un index par défaut    
            curIdxExu = self.dockwidget.list_exu.currentIndex()
        else: #on définit l'index sur l'identifiant sauvegardé
            # on recherche l'identifiant du layer dans les données de la combo 
            curIdxExu = self.dockwidget.list_exu.findData(exulyrId)
            if curIdxExu >= 0: # si la valeur recherché est trouvée
            # on défini l'index courrant sur le layer exutoire
                self.dockwidget.list_exu.setCurrentIndex(curIdxExu)


        
        try : # puis Bassin versant. On test que l'identifiant est définit
            bvlyrId
        except NameError:
            # On défini un index par défaut    
            curIdxBv = self.dockwidget.list_bv.currentIndex()            
        else: #on définit l'index sur l'identifiant sauvegardé
            # on recherche l'identifiant du layer dans les données de la combo 
            curIdxBv = self.dockwidget.list_bv.findData(bvlyrId)
            if curIdxBv >= 0:
            # on défini l'index courrant sur le layer Bassin versant
                self.dockwidget.list_bv.setCurrentIndex(curIdxBv)




    def selectionConnectByLayerIdx(self,layer): 
        """ 
            effectue la connection du Signal de changement de sélection sur une couche (par son index)
            récupère les entités sélectionnées de la couche et leurs info
        """
        #lyr = self.getLayerByIdx(layerIdx) # on prend le layer à partir de son index 

        #self.getInfoFronSelectionInLayer(lyr) # on prend les info à partir de la sélection du layer

        QObject.connect(layer, SIGNAL("selectionChanged()"), self.listen_SelectionChange)
    
    def getLayerIdxByName(self, layerName):
        layers = self.iface.legendInterface().layers()
        QgsMessageLog.logMessage("getLayerIdxByName : " + str(layerName), "Dessiner_entite_jointe")
        

        for layer in self.iface.legendInterface().layers():
            if layerName == layer.name():
                selectedLayer = layerName

        return selectedLayer


    def getLayerByIdx(self, layerIdx):
        layers = self.iface.legendInterface().layers()#liste des layers dans l'interface
        selectedLayer = layers[layerIdx] # définition du layer par son index
        return selectedLayer


    def getInfoFronSelectionInLayer(self, layer):

        selectedFeatures = self.getSelectFeature(layer) # on prend les sélections à partir du layer
        if selectedFeatures is not None:
            if len(selectedFeatures) >= 1:    
                info = self.getSelectedFeaturesInfo(selectedFeatures) # on prend les info de la couche
                return info
            else:            
                QgsMessageLog.logMessage(u"il faut sélectionner au moins 1 entité ", "Dessiner_entite_jointe")
                self.dockwidget.attribut_id.setText("")
                self.dockwidget.attribut_superficie.setText("")
    
    def getSelectFeature(self,layer):
        # récupérer les info du point sélectionné à partir de l'index de la liste de couche (dans la combobox) 
        #exuLyr = self.getLayerByIdx(getLyrIdx(list_exu))
        #QgsMessageLog.logMessage(str(layer), "Dessiner_entite_jointe")

        #on test que la couche est bien définie dans la liste
        if layer is not None:
            if layer.isValid():
            # La sélection est donc probable sur la couche
                selectedFeatures = layer.selectedFeatures()
                
                if selectedFeatures is not None:
                    #QgsMessageLog.logMessage(u"selectedFeatures " + str(selectedFeatures), "Dessiner_entite_jointe")

                    if len(selectedFeatures) > 1:
                        QgsMessageLog.logMessage(u"trop d'exutoire selectionnés : "+str(selectedFeatures), "Dessiner_entite_jointe")
                    elif len(selectedFeatures) == 0:
                        QgsMessageLog.logMessage(u"aucun exutoire sélectionné", "Dessiner_entite_jointe")
                    else:
                        QgsMessageLog.logMessage(u"exutoire selectionné : "+ str(selectedFeatures), "Dessiner_entite_jointe")
                        return None

                return selectedFeatures

    
    def getSelectedFeaturesInfo(self, selectedFeatures):

        #champs exutoires. Evo : à mettre dans une liste (un fichier etC... et à passer en argument)
        exu_id = "ID_BNBD"
        exu_superficie = "SUPERFICIE"
        exu_aval = "EXU_AVAL"

        val_exu_id = self.getFirstEntityAttributValue(selectedFeatures, exu_id)
        val_exu_superficie = self.getFirstEntityAttributValue(selectedFeatures, exu_superficie)

        self.dockwidget.attribut_id.setText(str(val_exu_id))
        self.dockwidget.attribut_superficie.setText(str(val_exu_superficie))

        return val_exu_id

    def getFirstEntityAttributValue(self, selectedFeatures, attribut):
        # Evo : trier les valeurs par superficie décroissante et prendre uniquement le premier

        value = selectedFeatures[0][attribut]

        QgsMessageLog.logMessage("attributs : " + str(selectedFeatures[0][attribut]), "Dessiner_entite_jointe")

        return value

    def listen_SelectionChange(self): # je n'arrive pas à passer l'argument LyrIdx ici

        # on redefini les idx des layers (si différent)
        exuLyrIdx = self.dockwidget.list_exu.currentIndex()
        bvLyrIdx = self.dockwidget.list_bv.currentIndex()

        lyr = self.getLayerByIdx(exuLyrIdx) # on prend le layer à partir de son index

        self.getInfoFronSelectionInLayer(lyr) # on prend les info des entités sélectionnées de la couche


    def getJoinEntityById(self, joinLayer, pk):

        #champs BV . Evo : à mettre dans une liste (un fichier etC... et à passer en argument)
        bv_id = "IDENTIF"

        request = joinLayer.getFeatures( QgsFeatureRequest().setFilterExpression(  format(bv_id) + " = '{}' ".format(pk) ))

        joinLayer.selectByIds(  [ f.id() for f in request ] )

        # tester si aucun n'existe (probablement la couche bv n'est pas renseignée)
        features = joinLayer.selectedFeatures()

        return features



    def drawEntity(self):

        tmp_layer_name = "Dessin_" + self.dockwidget.attribut_id.text()

        pk = self.dockwidget.attribut_id.text()

        bvLyrIdx = self.dockwidget.list_bv.currentIndex()

        joinLayer = self.getLayerByIdx(bvLyrIdx) # on prend le layer à partir de son index 
        
        #on récupère les features et on dessine dans la couche temp
        features = self.getJoinEntityById(joinLayer, pk)

        cfeature = QgsFeature()
        cfeatures=[]
        
        
        for f in features:
            cfeature_Attributes=[]
            cfeature_Attributes.extend(f.attributes())
            cfeature.setGeometry(f.geometry())
            cfeature.setAttributes(cfeature_Attributes)
            cfeatures.append(cfeature)

        
        templayer = QgsVectorLayer('Polygon?crs=epsg:2154', tmp_layer_name, 'memory')
        dataProvider = templayer.dataProvider()
        templayer.startEditing()
        dataProvider.addFeatures(cfeatures)
        templayer.commitChanges()
        templayer.updateExtents()
        
        
        vlayer = QgsVectorLayer( "?layer=ogr:/data/myfile.shp", "myvlayer", "virtual" )
        QgsMapLayerRegistry.instance().addMapLayer(templayer)





        