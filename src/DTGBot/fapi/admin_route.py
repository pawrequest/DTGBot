from fastapi import APIRouter, Depends, HTTPException, Header

SECRET_TOKEN = 'YourSecretToken'


def verify_token(x_token: str = Header(...)):
    if x_token != SECRET_TOKEN:
        raise HTTPException(status_code=401, detail='Invalid or missing token')


router = APIRouter()


@router.get('/')
def admin_dashboard(verified: bool = Depends(verify_token)):
    # if not verified:
    #     raise HTTPException(status_code=401, detail='Invalid or missing token')
    return {'message': 'Welcome to the Admin Dashboard'}
