from sqlmodel import Field, Relationship, SQLModel, Session, create_engine

engine = create_engine('sqlite:///orm.db')

class Author(SQLModel, table=True):
    id: int| None = Field(default=None, primary_key=True)
    name: str = Field(max_length = 50)
    email: str = Field(max_length = 50)

    # Relationship to the Book model, setting up a one-to-many relationship
    # Relationship of author to books
    books: list["Book"] = Relationship(back_populates="author")

class Book(SQLModel, table=True):
    id: int| None = Field(default=None, primary_key=True)
    title: str = Field(max_length=100)
    content: str
    author_id: int = Field(foreign_key="author.id")

    # Relationship of books to Author
    author: Author = Relationship(back_populates="books")

SQLModel.metadata.create_all(engine)

with Session(engine) as session:
    author1 = Author(name='Alice', email='alice@gmail.com')
    author2 = Author(name='Bob', email='bob@example.com')
    book1 = Book(title='Alice\'s First Book', content='This is the content of Alice\'s first book', author = author1)
    book2 = Book(title='Alice\'s Second Book', content='This is the content of Alice\'s second book', author = author1)
    book3 = Book(title='Bob\'s First Book', content='This is the content of Bob\'s first book', author = author2)
    session.add_all([author1, author2, book1, book2, book3])
    session.commit()