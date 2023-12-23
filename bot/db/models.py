from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

DATABASE_URL = "sqlite+aiosqlite:///./tg_database.db"

engine = create_async_engine(DATABASE_URL, echo=True)
Base = declarative_base()
SessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class User(Base):


    __tablename__ = 'users'  

    id = Column(Integer, primary_key=True)
    group_name = Column(String)
    is_leader = Column(Boolean, default=False)


    @classmethod
    async def get_all_users(cls, session: AsyncSession):
        """Get all users from the database.

        Args:
            session (AsyncSession): The async session to use for the query.

        Returns:
            List[User]: A list of all users in the database.
        """
        async with SessionLocal() as session:
            result = await session.execute(select(cls))
            return result.scalars().all()
        
    @classmethod
    async def create_user(cls, session: AsyncSession, user_id: int, group: str, is_leader: bool):
        """
        Create a new user in the database.

        Args:
            user_id (int): The Telegram user ID.
            group (str): The name of the group the user is in.
            is_leader (bool): Whether the user is a group leader.

        Returns:
            User: The newly created user.
        """
        async with SessionLocal() as session:
            new_user = User(id=user_id, group_name=group, is_leader=is_leader)
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
            return new_user
        
    @classmethod
    async def get_user_by_id(cls, session: AsyncSession, user_id: int):
        """Get a user by their Telegram user ID.

        Args:
            user_id (int): The Telegram user ID.

        Returns:
            User: The user with the given ID, or None if no user was found.
        """
        async with SessionLocal() as session:
            result = await session.execute(select(User).filter_by(id=user_id))
            return result.scalars().first()


    @classmethod
    async def delete_user(cls, session: AsyncSession, user_id: int):
        """Delete a user from the database.
        
        Args:
            user_id (int): The Telegram user ID

        Returns:
            None
        """
        async with SessionLocal() as session:
            user = await cls.get_user_by_id(session, user_id)
            if user:
                await session.delete(user)
                await session.commit()

    @classmethod
    async def _get_user_group_name(cls, session: AsyncSession, user_id: int):
        """Get a user's group name."""

        async with SessionLocal() as session:
            result = await session.execute(select(User).filter_by(id=user_id))
            return result.scalars().first().group_name

    @classmethod
    async def _is_leader(cls, session: AsyncSession, user_id: int):
        async with SessionLocal() as session:
            result = await session.execute(select(User).filter_by(id=user_id))
            return result.scalars().first().is_leader





class GroupMessage(Base):
    __tablename__ = 'group_messages'  

    id = Column(Integer, primary_key=True)
    group_name = Column(String, unique=True)
    message = Column(String)


    @classmethod
    async def get_group_messages(cls, session: AsyncSession, group_name: str):
        """
        Get all group messages from the database.
        """
        async with SessionLocal() as session:
            result = await session.execute(select(cls).filter_by(group_name=group_name))
            return result.scalars().all()

    @classmethod
    async def create_group_message(cls, session: AsyncSession, group_name: str, message: str):
        """
        Create a new group message in the database.
        """
        async with SessionLocal() as session:
            new_group_message = GroupMessage(group_name=group_name, message=message)
            session.add(new_group_message)
            await session.commit()
            await session.refresh(new_group_message)
            return new_group_message

    @classmethod
    async def delete_group_message(cls, session: AsyncSession, group_name: str):
        """
        Delete a group message from the database.
        """
        group_message = await cls.get_group_messages(session, group_name)
        if group_message:
            for message in group_message:
                session.delete(message)
            
            try:
                await session.commit()
            except Exception as e:
                return None
        else:
            return None
        
    @classmethod
    async def _create_group(cls, session: AsyncSession, group_name: str):
        async with SessionLocal() as session:
            try:
                new_group = GroupMessage(group_name=group_name)
                session.add(new_group)
                await session.commit()
                await session.refresh(new_group)
                return new_group
            except IntegrityError:
                return None






async def init_db():
    """
    Initialize the database.

    This function creates all the tables and relationships defined in the
    SQLAlchemy models. It should be called once at the start of the application
    to ensure that the database is set up correctly.

    Returns:
        None
    """
    async with engine.begin() as conn:

        await conn.run_sync(Base.metadata.create_all)
