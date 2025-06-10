from app.crud.crud_user import CRUDUser
from app.crud.crud_analysis import CRUDAnalysis  
from app.crud.review_crud import reviews

from app.models.user import User
from app.models.analysis import AnalysisRequest

user = CRUDUser(User)
analysis = CRUDAnalysis(AnalysisRequest) 