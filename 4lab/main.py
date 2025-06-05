from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime

app = FastAPI()

# Модели данных
class Author(BaseModel):
    id: int
    name: str

class Book(BaseModel):
    id: int
    title: str
    year: int
    author_id: int
    
    @field_validator('year')
    def year_must_be_valid(cls, v):
        current_year = datetime.now().year
        if v > current_year:
            raise ValueError('Год издания не может быть в будущем')
        return v

authors_db = [
    Author(id=1, name="Лев Толстой"),
    Author(id=2, name="Фёдор Достоевский")
]

books_db = [
    Book(id=1, title="Война и мир", year=1869, author_id=1),
    Book(id=2, title="Анна Каренина", year=1877, author_id=1),
    Book(id=3, title="Преступление и наказание", year=1866, author_id=2)
]

# Валидационные модели для запросов
class AuthorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class AuthorUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class BookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    year: int
    author_id: int

# API для авторов
@app.get("/authors", response_model=List[Author])
def get_authors():
    return authors_db

@app.post("/authors", response_model=Author, status_code=status.HTTP_201_CREATED)
def create_author(author: AuthorCreate):
    new_id = max(author.id for author in authors_db) + 1 if authors_db else 1
    new_author = Author(id=new_id, name=author.name)
    authors_db.append(new_author)
    return new_author

@app.get("/authors/{author_id}", response_model=Author)
def get_author(author_id: int):
    author = next((a for a in authors_db if a.id == author_id), None)
    if not author:
        raise HTTPException(status_code=404, detail="Автор не найден")
    return author

@app.put("/authors/{author_id}", response_model=Author)
def update_author(author_id: int, author_data: AuthorUpdate):
    author = next((a for a in authors_db if a.id == author_id), None)
    if not author:
        raise HTTPException(status_code=404, detail="Автор не найден")
    
    author.name = author_data.name
    return author

@app.delete("/authors/{author_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_author(author_id: int):
    global authors_db, books_db
    author = next((a for a in authors_db if a.id == author_id), None)
    if not author:
        raise HTTPException(status_code=404, detail="Автор не найден")
    
    books_db = [b for b in books_db if b.author_id != author_id]
    authors_db = [a for a in authors_db if a.id != author_id]
    return None

# API для книг
@app.get("/books", response_model=List[Book])
def get_books(author_id: Optional[int] = None):
    if author_id:
        return [b for b in books_db if b.author_id == author_id]
    return books_db

@app.post("/books", response_model=Book, status_code=status.HTTP_201_CREATED)
def create_book(book: BookCreate):
    if not any(a.id == book.author_id for a in authors_db):
        raise HTTPException(status_code=404, detail="Автор не найден")
    
    try:
        validated_book = Book(
            id=max(b.id for b in books_db) + 1 if books_db else 1,
            title=book.title,
            year=book.year,
            author_id=book.author_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    books_db.append(validated_book)
    return validated_book
