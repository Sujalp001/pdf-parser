from pathlib import Path


def make_pdf(path, text_lines, table=None):
    content = []
    content.append('BT')
    content.append('/F1 12 Tf')
    for x, y, text in text_lines:
        content.append(f'1 0 0 1 {x} {y} Tm')
        content.append(f'({text}) Tj')
    content.append('ET')
    if table:
        content.append('0.5 w')
        for y in table['hlines']:
            content.append(f'{table[1]} {y} m {table[2]} {y} l S')
        for x in table['vlines']:
            content.append(f'{x} {table[1]} m {x} {table[3]} l S')
        content.append('BT')
        content.append('/F1 10 Tf')
        for x, y, text in table['rows']:
            content.append(f'1 0 0 1 {x} {y} Tm')
            content.append(f'({text}) Tj')
        content.append('ET')
    stream = '\n'.join(content).encode('latin1')
    objs = []
    objs.append('<< /Type /Catalog /Pages 2 0 R >>')
    objs.append('<< /Type /Pages /Kids [3 0 R] /Count 1 >>')
    resources = '<< /Font << /F1 4 0 R >> >>'
    page = f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources {resources} /Contents 5 0 R >>'
    objs.append(page)
    objs.append('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>')
    objs.append(f'<< /Length {len(stream)} >>\nstream\n'.encode('latin1') + stream + b'\nendstream')

    data = b'%PDF-1.4\n'
    offsets = []
    for i, obj in enumerate(objs, start=1):
        offsets.append(len(data))
        if isinstance(obj, bytes):
            data += f'{i} 0 obj\n'.encode('latin1') + obj + b'\nendobj\n'
        else:
            data += f'{i} 0 obj\n{obj}\nendobj\n'.encode('latin1')
    xref = b'xref\n0 %d\n0000000000 65535 f \n' % (len(objs) + 1)
    for off in offsets:
        xref += f'{off:010d} 00000 n \n'.encode('latin1')
    trailer = f'trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{len(data)}\n%%EOF\n'.encode('latin1')
    data += xref + trailer
    path.write_bytes(data)

invoice_lines = [
    (50, 740, 'Invoice No: INV-001'),
    (50, 720, 'Date: 2026-05-25'),
    (50, 700, 'Vendor: Example Company'),
]
card_table = {
    1: 50, 2: 550, 3: 50, 4: 620,
    'vlines': [50, 250, 400, 550],
    'hlines': [620, 590, 560, 530, 500],
    'rows': [
        (55, 605, 'Description'), (255, 605, 'Qty'), (405, 605, 'Amount'),
        (55, 575, 'Widget A'), (255, 575, '2'), (405, 575, '$100'),
        (55, 545, 'Widget B'), (255, 545, '3'), (405, 545, '$150'),
        (55, 515, 'Service Fee'), (255, 515, '1'), (405, 515, '$50'),
    ]
}

bank_lines = [
    (50, 740, 'Bank Statement'),
    (50, 720, 'Account Number: 1234567890'),
    (50, 700, 'Period: 01-May-2026 to 25-May-2026'),
]
bank_table = {
    1: 50, 2: 550, 3: 50, 4: 620,
    'vlines': [50, 300, 420, 550],
    'hlines': [620, 590, 560, 530, 500],
    'rows': [
        (55, 605, 'Date'), (305, 605, 'Description'), (425, 605, 'Amount'),
        (55, 575, '01-May-2026'), (305, 575, 'Deposit'), (425, 575, '+$500'),
        (55, 545, '05-May-2026'), (305, 545, 'Withdrawal'), (425, 545, '-$120'),
        (55, 515, '20-May-2026'), (305, 515, 'Payment'), (425, 515, '-$80'),
    ]
}

root = Path('.')
make_pdf(root / 'sample_invoice.pdf', invoice_lines, card_table)
make_pdf(root / 'sample_bank_statement.pdf', bank_lines, bank_table)
print('Created sample_invoice.pdf and sample_bank_statement.pdf')
