export function Footer() {
  return (
    <footer className="border-t border-border dark:border-dark-border py-6 mt-8 transition-colors duration-200">
      <div className="max-w-[1200px] mx-auto px-8 text-center flex justify-center items-center gap-4 text-sm text-text-secondary dark:text-dark-text-secondary">
        <p>&copy; {new Date().getFullYear()} AI Melody Generator</p>
        <span className="text-border dark:text-dark-border">|</span>
        <a
          href="https://github.com/niallone/melodygenerator"
          target="_blank"
          rel="noopener noreferrer"
          className="hover:text-primary dark:hover:text-primary-light transition-colors"
        >
          GitHub
        </a>
      </div>
    </footer>
  );
}
