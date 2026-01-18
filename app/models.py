# app/models.py добавить:
class PromoCode(Base):
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    discount_percent = Column(Integer, default=0)
    discount_amount = Column(Float, default=0)
    valid_from = Column(DateTime)
    valid_to = Column(DateTime)
    max_uses = Column(Integer, default=1)
    used_count = Column(Integer, default=0)