class Book:
    def __init__(
        self,
        book_id: int | None,
        title: str,
        author: str,
        category: str,
        publisher: str | None = None,
        publication_year: int | None = None,
        status: str = "Available",
        quantity: int = 0,
        available_quantity: int | None = None
    ):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.category = category
        self.publisher = publisher
        self.publication_year = publication_year
        self.status = status
        self.quantity = int(quantity) if quantity is not None else 0
        self.available_quantity = (
            int(available_quantity) if available_quantity is not None else self.quantity
        )

    def to_dict(self) -> dict:
        """Trả về dictionary đúng chuẩn key quy định trong API Contract"""
        return {
            "book_id": int(self.book_id) if self.book_id is not None else None,
            "title": self.title,
            "author": self.author,
            "category": self.category,
            "publisher": self.publisher,
            "publication_year": int(self.publication_year) if self.publication_year is not None else None,
            "status": self.status,
            "total_quantity": self.quantity,
            "available_quantity": max(0, self.available_quantity)
        }