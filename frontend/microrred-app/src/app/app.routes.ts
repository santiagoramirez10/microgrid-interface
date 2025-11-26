import { Routes } from '@angular/router';
import { SizingComponent } from './pages/sizing/sizing';

export const routes: Routes = [
  {
    path: '',
    component: SizingComponent,
  },
  {
    path: '**',
    redirectTo: '',
  },
];
