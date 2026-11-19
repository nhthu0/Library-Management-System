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
        quantity: int = 0,
        available_quantity: int | None = None,
    ):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.category = category
        self.publisher = publisher
        self.publication_year = publication_year
        self.status = status
        self.quantity = quantity
        self.available_quantity = available_quantity

    def to_dict(self) -> dict:
        qty = int(self.quantity) if self.quantity is not None else 0
        available_qty = qty if self.available_quantity is None else int(self.available_quantity)
        available_qty = max(0, min(qty, available_qty)) if self.status == "Available" else 0
        return {
            "book_id": int(self.book_id) if self.book_id is not None else None,
            "title": self.title,
            "author": self.author,
            "category": self.category,
            "publisher": self.publisher,
            "publication_year": int(self.publication_year) if self.publication_year is not None else None,
            "status": "Available" if available_qty > 0 else "Unavailable",
            "quantity": qty,
            "total_quantity": qty,
            "available_quantity": available_qty
        }
