from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from . import models
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


app.mount("/static", StaticFiles(directory="static"), name="static")


templates = Jinja2Templates(directory="templates")
templates.env.globals["imgix_url"] = imgix_create_url


@app.get("/")
async def get_index(
    request: Request,
    db: Session = Depends(get_db),
    flokkur: str = None,
    verslun: str = None,
    verdbil: int = None,
):
    models_ = db.query(models.Model).filter(models.Model.active == True)

    if flokkur is not None:
        vclass = getattr(models.VehicleClassEnum, flokkur)
        if vclass is not None:
            if vclass in lett_bifhjol_classes:
                models_ = models_.filter(
                    models.Model.classification.in_(lett_bifhjol_classes)
                )
            else:
                models_ = models_.filter(models.Model.classification == vclass)

    retailer_counts = get_retailer_counts(db, models_)
    price_range_counts = get_price_range_counts(db, models_)

    if verslun is not None:
        models_ = models_.join(models.Retailer).filter(models.Retailer.slug == verslun)

    if verdbil is not None:
        try:
            price_min, price_max = price_ranges[verdbil]
        except IndexError:
            pass
        else:
            if price_min is not None:
                models_ = models_.filter(models.Model.price >= price_min)
            if price_max is not None:
                models_ = models_.filter(models.Model.price <= price_max)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "classification_counts": get_classification_counts(db),
            "retailer_counts": retailer_counts,
            "price_range_counts": price_range_counts,
            "models": models_.order_by(models.Model.price),
        },
    )


@app.get("/hjol/{id}")
async def get_model(request: Request, id: int, db: Session = Depends(get_db)):
    model = (
        db.query(models.Model)
        .filter(models.Model.active == True, models.Model.id == id)
        .first()
    )
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return templates.TemplateResponse(
        "model.html",
        {
            "request": request,
            "model": model,
            "classification_counts": get_classification_counts(db),
        },
    )
