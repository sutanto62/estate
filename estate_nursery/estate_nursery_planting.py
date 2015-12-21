from openerp import models, fields, api, exceptions


class Planting(models.Model):
    #seed planting
    _name = "estate.nursery.planting"

class PlantingLine(models.Model):

    _name = "estate.nursery.plantingline"

class Requestplanting(models.Model):

    _name = "estate.nursery.request"

class TrasferSeed(models.Model):

    _name = "estate.nursery.trasfer"

