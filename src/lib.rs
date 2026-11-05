#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Slide {
    pub title: String,
    pub content: String,
}

#[derive(Debug, Default)]
pub struct PresentationDeck {
    slides: Vec<Slide>,
    current_index: usize,
}

impl PresentationDeck {
    pub fn new() -> Self { Self { slides: Vec::new(), current_index: 0 } }
    pub fn add_slide(&mut self, title: &str, content: &str) {
        self.slides.push(Slide { title: title.into(), content: content.into() });
    }
    pub fn next_slide(&mut self) {
        if self.current_index + 1 < self.slides.len() {
            self.current_index += 1;
        }
    }
    pub fn current_slide(&self) -> Option<&Slide> {
        self.slides.get(self.current_index)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn test_presentation_deck_navigation_aaa() {
        // Arrange
        let mut deck = PresentationDeck::new();
        deck.add_slide("Slide 1", "Welcome to SigmaOS");
        deck.add_slide("Slide 2", "Architecture Overview");
        // Act
        assert_eq!(deck.current_slide().unwrap().title, "Slide 1");
        deck.next_slide();
        // Assert
        assert_eq!(deck.current_slide().unwrap().title, "Slide 2");
    }
}
