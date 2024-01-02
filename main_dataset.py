"""
Database have atomic structure as a *.cif file for 528 different materials. Also, it contains some other physical
properties such as Photoluminescence or band gap. This script demonstrate how to download some dataset from website
"""


import requests, time
from IPython.display import display
import pandas as pd


responseURL = requests.get('https://materials.hybrid3.duke.edu/materials/systems/')
dictMaterial = responseURL.json()
print("Total number of material:", dictMaterial['count'])

responseURL = requests.get('https://materials.hybrid3.duke.edu/materials/properties/')
dictProperty = responseURL.json()

#list of properties measured for all materials. Each material usually have 1-4 property from the list
propertydf = pd.DataFrame(dictProperty['results'])
display(propertydf)




class datasetOneMaterial(object):
    """ Class to collect data for one material from database in some standart format"""
    def __init__(self, idxMaterial):
        self.idxMaterial = idxMaterial

        self.infoMaterial = dictMaterial['results'][idxMaterial]
        self.realIdxMaterial =  self.infoMaterial['pk']
        self.formula = self.infoMaterial['formula']
        self.organic = self.infoMaterial['organic']
        self.inorganic = self.infoMaterial['inorganic']
        self.urlProperty = 'https://materials.hybrid3.duke.edu/materials/{}'.format(self.realIdxMaterial)
        self.listDataset, self.countProperty = self._getDataset()
        self.listPropertyData = self.getListProperty()

    def getDataForDataFrame(self):
        d = {}
        d['idMaterial'] = self.realIdxMaterial
        d['formula'] = self.formula
        d['organic'] = self.organic
        d['inorganic'] = self.inorganic
        d['property'] = self.listPropertyData
        return d



    def _getDataset(self):
        # To get avaliable dataset for material we need request it as follows:
        url = 'https://materials.hybrid3.duke.edu/materials/datasets/?system={}'.format(self.realIdxMaterial)
        responseURL = requests.get(url)
        return (responseURL.json())['results'], (responseURL.json())['count']

    def getListProperty(self):
        listProperty = []
        for i in self.listDataset:
            urlProperty = 'https://materials.hybrid3.duke.edu/materials/datasets/{}/files/'.format(i['pk'])
            # For primary: [id,  Name, unit, value]. For secondary: [id,  Name, unit, value] or [None]
            dictProperty = {'url':urlProperty, 'primary_property': {}, 'secondary_property': {}}
            dictProperty['primary_property']['id'] = i['primary_property']['id']  # property id
            dictProperty['primary_property']['name'] = i['primary_property']['name'] # property name

            if i['primary_unit'] is not None:
                dictProperty['primary_property']['unit'] = i['primary_unit']['label']  # unit
            else: dictProperty['primary_property']['unit'] = None

            datalistPrimary, datalistSecondary = [], []
            if i['primary_property']['name'] != 'atomic structure':
                for x in i['subsets'][0]['datapoints']: # x is list with qualifier
                    for data in x['values']:
                        if data['qualifier'] == 'secondary': datalistSecondary.append(data['formatted'])
                        if data['qualifier'] == 'primary': datalistPrimary.append(data['formatted'])

                dictProperty['primary_property']['data'] = datalistPrimary  # data
            else:
                dictProperty['primary_property']['data'] = 'Only file'  # data

            if i['secondary_property'] is None:
                dictProperty['secondary_property'] = None
            else:
                dictProperty['secondary_property']['id'] = i['secondary_property']['id']  #property id
                dictProperty['secondary_property']['name'] = i['secondary_property']['name'] #property name
                dictProperty['secondary_property']['unit'] = i['secondary_unit']['label']  # unit
                dictProperty['secondary_property']['data'] = datalistSecondary  # data
            listProperty.append(dictProperty)
        return listProperty

    def printInfoMaterial(self):
        print("\nThe url with API for material under number {} is available at:\n".format(self.idxMaterial), self.urlProperty)

        print("\nExample of info about material number:", self.idxMaterial)
        for k, v in self.infoMaterial.items():
            print(k, ':\t', v)

    def printInfoDataset(self, info = 'brief'):
        if info == 'brief':
            print("\nThere are {} results for this material, avaliable at {}:".format(self.countProperty,
                                                                                      self.urlProperty))
        elif info == 'expanded':
            print("\n Data for specific property:")

        for item in self.listPropertyData:
            name1, unit1 = item['primary_property']['name'], item['primary_property']['unit']
            name2 = None if item['secondary_property'] is None else item['secondary_property']['name']
            unit2 = None if item['secondary_property'] is None else item['secondary_property']['unit']

            if info == 'brief':
                print("{}({}) vs {}({})".format(name1, unit1, name2, unit2))

            if info == 'expanded':
                print("{}({}) vs {}({}). Data also available at url:{}".format(name1, unit1, name2, unit2, item['url']))
                print("\n Data for this property:")
                print('{}({})'.format(name1, unit1),':\n',item['primary_property']['data'])
                if item['secondary_property'] is not None:
                    print('{}({})'.format(name2, unit2),':\n',item['secondary_property']['data'])
                print("\n --------------------------------------------")

class makeDataFrame(object):
    """Class to build dictionary for dataframe"""
    def __init__(self, listData):
        self.listData = listData
        self.dataFrame = {
            'idMaterial': [],
            'formula': [],
            'organic': [],
            'inorganic': []
        }
        self.total = 0

        #add each material to dataframe
        for i in self.listData:
            self.addMaterialToDataFrame(i)

    def addMaterialToDataFrame(self, singleMaterial):
        new_key = []
        new_value = []

        for key, item in singleMaterial.items():

            if key != 'property':
                new_key.append(key)
                new_value.append(item)
            if key == 'property':
                for prop in singleMaterial['property']:
                    id = prop['primary_property']['id']
                    name = prop['primary_property']['name']
                    unit = prop['primary_property']['unit']
                    # length = len(prop['primary_property']['data'])
                    newPropName = '{}({})'.format(name, id)

                    if newPropName not in new_key: # !!! exclude duplication of the data
                        new_key.append('{}({})'.format(name, id))
                        # new_value.append('{}:len={}'.format(unit, length))
                        if name == 'atomic structure':
                            new_value.append('file')
                        else:
                            new_value.append('Unit: {}'.format(unit))

        #add to global DataFrame
        for keyDF, itemDF in self.dataFrame.items():
            if keyDF in new_key:
                indx = new_key.index(keyDF)
                itemDF.append(new_value[indx])
                del new_value[indx]
                del new_key[indx]
            else:
                itemDF.append(None)

        self.total +=1
        #add new element
        for key, value in zip(new_key, new_value):
            self.dataFrame[key] = []
            for i in range(0,self.total-1):
                self.dataFrame[key].append(None)
            self.dataFrame[key].append(value)




idxMaterial = 20  #put any number between [1, 529]
oneMaterial = datasetOneMaterial(idxMaterial)
oneMaterial.printInfoMaterial()
oneMaterial.printInfoDataset(info='brief')
oneMaterial.printInfoDataset(info='expanded')


#build dataframe for one material
listTreatedMaterials = [datasetOneMaterial(20).getDataForDataFrame()]
dataFrame = makeDataFrame(listTreatedMaterials)
df = pd.DataFrame(dataFrame.dataFrame)
display(df)



# example of dataFrame for 50 materials.
# Make request for each material is too long, so data are uploaded from file
import pickle
with open('datasetPerovskite_1_50.pickle', 'rb') as handle:
    listTreatedMaterials_50 = pickle.load(handle)

dataFrame = makeDataFrame(listTreatedMaterials_50)
df_50 = pd.DataFrame(dataFrame.dataFrame)
display(df_50)










