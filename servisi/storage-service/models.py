from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Index, func
from typing import Optional, List



class Base(DeclarativeBase):
    pass


class Sensor(Base):
    __tablename__="sensors"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    data: Mapped[List["SensorData"]] = relationship(
        back_populates="sensor", 
        cascade="all, delete-orphan", 
        passive_deletes=True,
    )


class SensorData(Base):
    __tablename__="sensor_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sensor_id: Mapped[str] = mapped_column(
        String, ForeignKey("sensors.id", ondelete="CASCADE"), index=True
    )
    timestamp: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    temperature: Mapped[float] = mapped_column(Float, nullable=False)
    aqi: Mapped[float] = mapped_column(Float, nullable=False)

    sensor: Mapped["Sensor"] = relationship(back_populates="data")


Index("ix_sensor_time", SensorData.sensor_id, SensorData.timestamp.desc())