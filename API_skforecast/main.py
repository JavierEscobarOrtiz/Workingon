from fastapi import FastAPI, Request
from pydantic import BaseModel, validator
import pandas as pd
from skforecast.utils import load_forecaster
from google.cloud import bigquery as bq
from google.oauth2 import service_account

# uvicorn main:app --reload 
# http://127.0.0.1:8000/make_preds
class Last_window(BaseModel):
    y: dict

    @validator("y")
    def y_must_be_dict_of_str_float(cls, value):
        if not isinstance(value, dict):
            raise TypeError(
                ("`last_window` argument must be a dict in the form `{index: float}`. " 
                 f"Got {type(value)}.")
            )
        if not all(isinstance(x, float) for x in value.values()):
            raise TypeError(
                ("`last_window` values must be float.")
            )
        if not all(isinstance(x, str) for x in value.keys()):
            raise TypeError(
                ("`last_window` keys must be string.")
            )

        return value

app = FastAPI()

@app.get("/")
def root():
    return {"message": "hello world again"}


@app.post("/make_preds/")
def make_preds(last_window: Last_window):
    """
    Create predictions using a `last_window`.
    """
    # read JSON
    lw = pd.Series(last_window.y)
    lw.index = pd.to_datetime(lw.index)
    lw = lw.asfreq('MS')

    # Read BQ
    client = bq.Client()

    query_exog_test = """
    SELECT *
    FROM `ingka-food-analytics-prod.forecast_models.test_javi`
    """

    df_exog_test = client.query(query_exog_test).result().to_dataframe()
    df_exog_test = df_exog_test.set_index('idx')
    df_exog_test = df_exog_test.asfreq('MS')

    # Load forecaster
    forecaster_loaded = load_forecaster('forecaster.py', verbose=False)
    
    # Make Predictions
    pred = forecaster_loaded.predict(
               steps       = 3,
               last_window = lw,
               exog        = df_exog_test[['exog_1', 'exog_2']]
           )

    return {"pred": pred}