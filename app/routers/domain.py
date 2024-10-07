from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..dependencies import get_current_user, get_db
from ..app_data import crud, schemas
from typing import Annotated

router = APIRouter()


@router.post("/user/check_subdomain_availability/", response_model=schemas.SubdomainAvailability)
async def check_subdomain_availability(
    current_user: Annotated[schemas.UserAuthenticate, Depends(get_current_user)],
    subdomain: schemas.SubdomainCreate,
    db: Session = Depends(get_db),
):
    # user_subdomains = crud.get_user_subdomains(db, current_user.id)
    # if len(user_subdomains) >= 5:
    #     raise HTTPException(status_code=400, detail="You have reached the maximum limit of 5 subdomains")
    
    # Check if the domain exists in the Domain table
    domain = crud.get_domain_by_name(db, subdomain.domain_name)
    if not domain:
        raise HTTPException(status_code=400, detail="The specified domain does not exist")

    existing_subdomain = crud.get_subdomain_by_name_and_domain(db, subdomain.name, subdomain.domain_name)
    if existing_subdomain:
        if existing_subdomain.user_id == current_user.id:
            return {"is_available": False, "message": "You already own this subdomain"}
        else:
            return {"is_available": False, "message": "This subdomain is not available"}
    
    return {"is_available": True, "message": "This subdomain is available"}

@router.get("/user/domains/", response_model=list[schemas.SubdomainCreate])
async def get_user_domains(
    current_user: Annotated[schemas.UserAuthenticate, Depends(get_current_user)],
    db: Session = Depends(get_db)):
    user_domains = crud.get_user_domains(db, current_user.id)
    return user_domains