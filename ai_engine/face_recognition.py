from sqlalchemy import Integer, String, Column, Float, Text, DateTime
from sqlalchemy import declarative_base
from database.base import Base


class my_class(object):
    pass

class face_recognition(Base):

    __tablename__ = 'Face Recognition'

    recognition_id = Column(Integer, primary_key=True)

    case_id = Column(Integer)

    camera_id= Column(Integer)

    image_url = Column(Text)

    recognized_person = Column(String(100))

    confidence_score = Column(Float)

    recognition_time = Column(DateTime) 


