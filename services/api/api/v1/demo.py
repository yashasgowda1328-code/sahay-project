from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from simulator.demo import start_demo, tick_demo, reset_demo, get_demo_state, DEMO_CASE_ID

router = APIRouter()


class DemoStartResponse(BaseModel):
    case_id: str
    phase: int
    status: str
    message: str


class DemoTickResponse(BaseModel):
    case_id: str
    phase: int
    status: str
    message: str
    priority: str
    details: str
    alert_count: int
    readings_added: int


class DemoStateResponse(BaseModel):
    case_id: str
    phase: int
    status: str


@router.post("/demo/start", response_model=DemoStartResponse)
async def start_demo_mode():
    result = await start_demo()
    return DemoStartResponse(**result)


@router.post("/demo/tick", response_model=DemoTickResponse)
async def tick_demo_mode():
    try:
        result = await tick_demo()
        return DemoTickResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/demo/reset")
async def reset_demo_mode():
    result = await reset_demo()
    return result


@router.get("/demo/state", response_model=DemoStateResponse)
async def get_demo_status():
    result = await get_demo_state()
    return DemoStateResponse(**result)


@router.get("/demo/case")
async def get_demo_case():
    return {"case_id": DEMO_CASE_ID}
