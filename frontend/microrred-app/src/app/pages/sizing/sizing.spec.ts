import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Sizing } from './sizing';

describe('Sizing', () => {
  let component: Sizing;
  let fixture: ComponentFixture<Sizing>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Sizing]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Sizing);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
