import os

os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = (
    "mysql+asyncmy://keyframe_user:keyframe_pass_51sut@127.0.0.1:3306/"
    "keyframe_workbench_test?charset=utf8mb4"
)
