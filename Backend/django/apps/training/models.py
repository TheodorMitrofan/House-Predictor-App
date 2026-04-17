import uuid
from django.db import models


class TrainingData(models.Model):
    """
    Dataset used to train the ML model.
    Columns match the Kaggle house_prices.csv dataset from the EDA notebook.
    """
    id = models.BigAutoField(primary_key=True, db_column="idL")
    date = models.DateField(blank=True, null=True)
    price = models.FloatField()
    bedrooms = models.IntegerField()
    bathrooms = models.IntegerField()
    sqft_living = models.IntegerField()
    sqft_lot = models.IntegerField()
    floors = models.FloatField()
    waterfront = models.BooleanField(default=False)
    view = models.IntegerField(default=0)
    condition = models.IntegerField()
    grade = models.IntegerField()
    sqft_above = models.IntegerField()
    sqft_basement = models.IntegerField()
    yr_built = models.IntegerField()
    yr_renovated = models.IntegerField(default=0)
    zipcode = models.IntegerField()
    lat = models.FloatField()
    long = models.FloatField()
    sqft_living15 = models.IntegerField()
    sqft_lot15 = models.IntegerField()

    class Meta:
        db_table = "training_data"


class RunHistory(models.Model):
    """
    One row per retrain run.
    model_path → MinIO URI e.g. s3://hpa-models/models/rf_20260416_120000.pkl
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateTimeField(auto_now_add=True)
    duration = models.DurationField(blank=True, null=True)
    accuracy = models.FloatField()
    dataset_size = models.BigIntegerField(db_column="datasetSize")
    success = models.BooleanField(default=False)
    model_path = models.CharField(max_length=500, db_column="modelPath", blank=True, null=True)
    is_active = models.BooleanField(default=False, db_column="isActive")
    version = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = "run_history"
        ordering = ["-date"]
