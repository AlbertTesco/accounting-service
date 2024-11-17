from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

Base = declarative_base()


class EmployeeORM(Base):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    rank = Column(String)

    projects = relationship("EmployeeProjectAssignmentORM", back_populates="employee")

    def __repr__(self):
        return f"EmployeeORM(id={self.id}, name={self.name}, rank={self.rank})"


class ProjectORM(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    parent_id = Column(Integer, ForeignKey('projects.id', ondelete="CASCADE"), nullable=True)

    parent = relationship(
        'ProjectORM',
        backref=backref(
            'subprojects',
            cascade="all, delete-orphan",
            passive_deletes=True
        ),
        remote_side=[id]
    )

    # Связь с промежуточной таблицей EmployeeProjectAssignmentORM
    employees = relationship("EmployeeProjectAssignmentORM", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"ProjectORM(id={self.id}, name={self.name}, parent_id={self.parent_id})"


class EmployeeProjectAssignmentORM(Base):
    __tablename__ = 'employee_project_assignments'

    employee_id = Column(Integer, ForeignKey('employees.id'), primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), primary_key=True)

    # Связь с моделями EmployeeORM и ProjectORM
    employee = relationship("EmployeeORM", back_populates="projects")
    project = relationship("ProjectORM", back_populates="employees")

    def __repr__(self):
        return f"EmployeeProjectAssignmentORM(employee_id={self.employee_id}, project_id={self.project_id})"
