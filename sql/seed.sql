
USE library_management;

-- Sample books
INSERT INTO books
(title, author, category, publisher,
 publication_year, status, quantity)
VALUES
('Clean Code', 'Robert C. Martin',
 'Programming', 'Prentice Hall', 2008,
 'Available', 5),

('Introduction to Algorithms',
 'Thomas H. Cormen', 'Computer Science',
 'MIT Press', 2009, 'Available', 3),

('Python Crash Course',
 'Eric Matthes', 'Programming',
 'No Starch Press', 2019, 'Available', 4),

('Design Patterns',
 'Erich Gamma', 'Software Engineering',
 'Addison-Wesley', 1994, 'Available', 2),

('Database System Concepts',
 'Abraham Silberschatz', 'Database',
 'McGraw-Hill', 2019, 'Available', 3);
