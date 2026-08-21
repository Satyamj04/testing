import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'VAPT Agent - AI-Powered Security Testing Platform',
  description: 'Production-grade AI-powered vulnerability assessment and penetration testing platform for authorized security testing.',
  keywords: 'VAPT, penetration testing, security, vulnerability assessment, AI, OWASP',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className={inter.className} style={{ backgroundColor: '#0a0c14', margin: 0 }}>
        {children}
      </body>
    </html>
  );
}
