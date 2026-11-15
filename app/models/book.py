class Book:
    def __init__(
        self,
        book_id: int | None = None,
        title: str = "",
        author: str = "",
        category: str = "",
        publisher: str | None = None,
        publication_year: int | None = None,
        status: str = "Available",
        quantity: int = 0
    ):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.category = category
        self.publisher = publisher
        self.publication_year = publication_year
        self.status = status
        self.quantity = quantity

    def to_dict(self) -> dict:
        qty = int(self.quantity) if self.quantity is not None else 0
        available_qty = qty if (self.status == "Available" and qty > 0) else 0
        return {
            "book_id": int(self.book_id) if self.book_id is not None else None,
            "title": self.title,
            "author": self.author,
            "category": self.category,
            "publisher": self.publisher,
            "publication_year": int(self.publication_year) if self.publication_year is not None else None,
            "status": self.status,
            "quantity": qty,
            "total_quantity": qty,
            "available_quantity": available_qty
        }