## THis is where we define what we want our output to be

from dataclasses import dataclass ## This is a kind of decorator that creates a variable for an empty class. It creates the constructor automatically. 

@dataclass
class DataIngestionArtifact:
    trained_file_path:str
    test_file_path:str

@dataclass
class DataValidationArtifact:
    validation_status: bool
    valid_train_file_path: str
    valid_test_file_path: str
    invalid_train_file_path: str
    invalid_test_file_path: str
    drift_report_file_path: str

@dataclass
class DataTransformationArtifact:
    transformed_object_file_path:str
    transformed_train_file_path:str
    transformed_test_file_path:str

# @dataclass
# class ClassificationMetricArtifact:
#     r2_score: float
#     rmse: float
#     recall_score: float

@dataclass
class PerformanceMetricArtifact:
    r2_score: float
    rmse: float

@dataclass
class ModelTrainerArtifact:
    trained_model_file_path:str
    trained_metric_artifact: PerformanceMetricArtifact
    test_metric_artifact: PerformanceMetricArtifact
