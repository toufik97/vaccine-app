from django.db import models

class Setting(models.Model):
    key = models.CharField(max_length=100, primary_key=True)
    value = models.TextField()

    class Meta:
        verbose_name = 'Setting'
        verbose_name_plural = 'Settings'

class VaccineFamily(models.Model):
    id_name = models.CharField(max_length=50, primary_key=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    linked_antigen_family = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = 'Vaccine Family'
        verbose_name_plural = 'Vaccine Families'

    def __str__(self):
        return self.display_name

class Milestone(models.Model):
    name = models.CharField(max_length=50, primary_key=True)
    target_days = models.IntegerField()
    order_index = models.IntegerField()

    class Meta:
        ordering = ['order_index']
        verbose_name = 'Milestone'
        verbose_name_plural = 'Milestones'

    def __str__(self):
        return self.name

class VaccineDose(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    family = models.ForeignKey(VaccineFamily, on_delete=models.CASCADE, related_name='doses')
    milestone = models.ForeignKey(Milestone, on_delete=models.CASCADE, related_name='doses')
    pneumo_protocol = models.CharField(max_length=20)
    min_age_days = models.IntegerField(default=0)
    offset_days = models.IntegerField(default=0)
    
    # New Admin-configurable properties
    administration_route = models.CharField(max_length=50, blank=True, null=True)
    default_injection_site = models.CharField(max_length=100, blank=True, null=True)
    vial_lifespan_days = models.IntegerField(default=0)
    
    advanced_rules_json = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Vaccine Dose'
        verbose_name_plural = 'Vaccine Doses'

    def __str__(self):
        return f"{self.id} ({self.milestone.name})"

class Patient(models.Model):
    id_label = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=200)
    dob = models.DateField()
    sexe = models.CharField(max_length=10) # 'M' or 'F'
    address = models.CharField(max_length=300, blank=True, null=True)
    parent_name = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    email = models.CharField(max_length=200, blank=True, null=True)

class PatientVaccine(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vaccines')
    milestone_name = models.CharField(max_length=100)
    vaccine_name = models.CharField(max_length=100)
    due_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=50)
    given_date = models.CharField(max_length=20, blank=True, null=True) # Could be "Inconnue" or date string
    observation = models.TextField(blank=True, null=True)
    
    # New Clinical Fields (Optional for legacy data compatibility)
    lot_number = models.CharField(max_length=100, blank=True, null=True)
    expiration_date = models.DateField(blank=True, null=True)
    diluent_confirmed = models.BooleanField(default=False, blank=True, null=True)
    injection_site = models.CharField(max_length=100, blank=True, null=True)
    eipv_notified = models.BooleanField(default=False)


class Visit(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='visits')
    visit_date = models.DateField()
    weight = models.FloatField(blank=True, null=True)
    height = models.FloatField(blank=True, null=True)
    imc = models.FloatField(blank=True, null=True)
