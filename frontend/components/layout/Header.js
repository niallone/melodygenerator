import Link from 'next/link';

export function Header() {
  return (
    <header className="bg-primary text-white py-4">
      <div className="max-w-[1200px] mx-auto px-8 flex justify-between items-center">
        <h1 className="text-xl m-0">AI Melody Generator</h1>
        <nav>
          <ul className="list-none p-0 m-0 flex">
            <li className="ml-4">
              <Link href="/" className="text-white no-underline hover:underline">Home</Link>
            </li>
            <li className="ml-4">
              <Link href="/about" className="text-white no-underline hover:underline">About</Link>
            </li>
          </ul>
        </nav>
      </div>
    </header>
  );
}
