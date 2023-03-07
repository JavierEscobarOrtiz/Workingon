from fastapi import FastAPI
import numpy as np
import pickle
import pandas as pd

app = FastAPI()

@app.post("/make_preds")
def make_preds(
  sq_mt:int, 
  n_bathrooms:int, 
  n_rooms:int, 
  has_lift:str, 
  house_type:str
):

  # Load Files
  encoder_fit = pd.read_pickle(r'./app/encoder.pickle')
  rf_reg_fit = pd.read_pickle(r'./app/model.pickle')

  # Create df
  x_pred = pd.DataFrame(
    [[sq_mt, n_bathrooms, n_rooms, bool(has_lift), house_type]],
    columns = ['sq_mt_built', 'n_bathrooms', 'n_rooms', 
               'has_lift', 'house_type_id']
    )

  # One hot encoding
  encoded_data_pred = pd.DataFrame(
    encoder_fit.transform(x_pred['house_type_id']),
    columns = encoder_fit.classes_.tolist()
  ) 

  # Build final df
  x_pred_transf = pd.concat(
    [x_pred.reset_index(), encoded_data_pred],
    axis = 1
  )\
  .drop(['house_type_id', 'index'], axis = 1)

  preds = rf_reg_fit.predict(x_pred_transf)

  return round(preds[0])