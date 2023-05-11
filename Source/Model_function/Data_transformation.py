import os
import sys
from Source.logger import logging
from Source.exception import CustomExceptionClass
from Source.utils import save_objects_file
from dataclasses import dataclass

import pandas as pd
import time
import nltk,string

nltk.download('stopwords')
nltk.download('wordnet')

from nltk import WordNetLemmatizer,PorterStemmer,wordpunct_tokenize
from nltk.corpus import stopwords

from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder,LabelEncoder,StandardScaler,MinMaxScaler,MaxAbsScaler,RobustScaler,FunctionTransformer


class CustomFunctionsClass:

    def nlp_function(NLP_Data):
        NLP_Data = NLP_Data['Issue'] 
        tokenized_data = NLP_Data.apply(lambda x: wordpunct_tokenize(x.lower()))

        def remove_punctuation(text):
            return [w for w in text if w not in string.punctuation]
        no_punctuation_data = tokenized_data.apply( lambda x: remove_punctuation(x))

        Stop_words = stopwords.words('english')
        Removed_Stopwords = [w for w in no_punctuation_data if not w in Stop_words]
        Removed_Stopwords = pd.Series(Removed_Stopwords)

        def lemmatize_text(text):
            lem_text = [WordNetLemmatizer().lemmatize(w,pos = 'v') for w in text]
            return lem_text
        lemmatized_data = Removed_Stopwords.apply(lambda x:lemmatize_text(x))

        def stem_text(text):
            stem_text = [PorterStemmer().stem(w) for w in text]
            return stem_text
        stemmed_data = lemmatized_data.apply(lambda x:stem_text(x))

        clean_data=[" ".join(x) for x in stemmed_data]
        logging.info("Text preprocessing succesfully done")
        logging.info("Returnnig preprocessed data")
        return clean_data

    
    def date_time_function(data):
        data['Date received']=pd.to_datetime(data['Date received'])
        data['Date sent to company']=pd.to_datetime(data['Date sent to company'])
        data['days_held']=(data['Date sent to company']-data['Date received']).dt.days
        return data['days_held'].values.reshape(-1,1)

@dataclass
class Data_transformation_config:

    data_transformation_file=os.path.join('Assets',"Data_Transformation.pkl")

class DataTransformClass:
    try:
        
        def get_data_transformation(self):
            
            start=time.time()

            logging.info("Data transformation started")
            Numerical_Column=[]
            Categorical_Column=['Product','Timely response?','Company response to consumer','Submitted via']
            NLP_Column=['Issue']
            Date_Time_Column=['Date sent to company','Date received']

            ## Pipelines 
            logging.info("Numerical pipeline initiated")
            Num_pipeline=Pipeline(steps=[
                                        ("Numerical_Imputer",SimpleImputer(strategy='median'))
                                        ,("Numerical_Scaler",MinMaxScaler())
                                        ])
            logging.info("Categorical pipeline initiated")
            Cat_pipeline=Pipeline( steps=[
                                        ("Categorical_Imputer",SimpleImputer(strategy='most_frequent'))
                                        ,('Categorical_Onehot',OneHotEncoder(sparse=False,drop='first'))
                                        ,("Categorical_Scaler",MinMaxScaler())
                                        ]) 
            logging.info("Nlp pipeline initiated")
            Nlp_pipline=Pipeline( steps=[
                                        ("Nlp_extration",FunctionTransformer(CustomFunctionsClass.nlp_function,validate=False))
                                        ,("CountVector",CountVectorizer())
                                        ,("NLP_Scaler",MaxAbsScaler())
                                        ])
            logging.info("Date_time pipeline initiated")
            Date_time_pipeline=Pipeline(steps=[
                                        ("Date_time_transformer",FunctionTransformer(CustomFunctionsClass.date_time_function,validate=False))
                                        ,("Date_time_Scaler",MinMaxScaler())
                                        ])

            logging.info("ColumnTransformer started running pipelines")    
            # Transformer for pipeline
            column_preprocessor=ColumnTransformer( 
                                        [
                                        ("Numerical_Transformer",Num_pipeline,Numerical_Column)
                                        ,("Categorical_Transformer",Cat_pipeline,Categorical_Column)
                                        ,('NLP_Transformer',Nlp_pipline,NLP_Column)
                                        ,("Date_time_Transfomer",Date_time_pipeline,Date_Time_Column)
                                        ]
                                        ,remainder='passthrough')# untoched column that are not transformed   
            logging.info("ColumnTransformer initiated pipelines succesfully") 
            end=time.time()
            logging.info("Data transformation initited succesfully in: {:.2f} seconds".format(end - start))
            return column_preprocessor

    except Exception as e:
          logging.error(str(e))
          raise CustomExceptionClass(e,sys.exc_info()) 

    try:
        
        def initiate_data_transformation(self,train_path,test_path):
            start = time.time()

            logging.info("Data transformation initiated")
            train_dataframe=pd.read_csv(train_path)
            test_dataframe=pd.read_csv(test_path)
            logging.info("Dataset successfully stored for transformatiom")

            Column_Preprocessor_Object=self.get_data_transformation()
            

            Train_features=train_dataframe.drop(columns=['Consumer disputed?'],axis=1)
            Train_target_feature=train_dataframe['Consumer disputed?']

            Test_features=test_dataframe.drop(columns=['Consumer disputed?'],axis=1)
            Test_target_feature=test_dataframe['Consumer disputed?']
            logging.info("Dataset succesfully coupled for training and testing phase")

            
            Label_encoder_object = LabelEncoder()
            logging.info("Starting column transformation on the dataset")
            Train_features_attr=Column_Preprocessor_Object.fit_transform(Train_features)
            Test_features_attr=Column_Preprocessor_Object.transform(Test_features)
            end = time.time()
           
            logging.info("Dataset transformation succesfully done transforming our dataset in: {:.2f} seconds".format(end - start))

            logging.info("Transforming our target data column")
            Train_target_attr = Label_encoder_object.fit_transform(Train_target_feature)
            Test_target_feature=Label_encoder_object.transform(Test_target_feature)
            logging.info("Target column transforming successfully done ")
                      

            logging.info("Saving the object file")
            save_objects_file(
                file_path=Data_transformation_config.data_transformation_file,
                object=Column_Preprocessor_Object

            )

            return(
                Train_features_attr,Train_target_attr,Test_features_attr,Test_target_feature
            )

    except Exception as e:
          logging.error(str(e))
          raise CustomExceptionClass(e,sys.exc_info()) 

        






